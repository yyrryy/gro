from django.shortcuts import render, redirect
from main.models import Produit, Mark, Category, Supplier, Stockin, Itemsbysupplier, Client, Represent, Order, Orderitem, Clientprices, Bonsortie, Facture, Outfacture, Livraisonitem, PaymentClientbl, PaymentClientfc,  PaymentSupplier, Bonsregle, Returnedsupplier, Avoirclient, Returned, Avoirsupplier, Orderitem, Carlogos, Ordersnotif, CommandItem, DeviItem, Sortieitem, Devi, Bonlivraison, Command, CommandItemsupplier, DeviItemsupplier, Devisupplier, Commandsupplier, Factureachat, Outfactureachat, Avanceclient
from django.http import JsonResponse, HttpResponse
import qrcode
from django.db.models import Count, F, Sum, Q, ExpressionWrapper, Func, fields, IntegerField
from datetime import datetime, date, timedelta
from django.utils import timezone
import json
from django.db import transaction
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
today = timezone.now().date()
thisyear=timezone.now().year

def checklivraisonno(request):
    no=request.GET.get('no')
    id=request.GET.get('id')
    bl=Bonlivraison.objects.exclude(pk=id).filter(bon_no=no).first()
    
    return JsonResponse({
        'exist':True if bl else False
    })

def checkfactureno(request):
    no=request.GET.get('no')
    id=request.GET.get('id')
    bl=Facture.objects.exclude(pk=id).filter(facture_no=no).first()
    
    return JsonResponse({
        'exist':True if bl else False
    })

def duplicate(request):
    ref=request.GET.get('ref')
    # check if ref already exists
    item=Produit.objects.filter(ref=ref).exists()
    if item:
        return JsonResponse({
            'exist':False,
            'message':'Reference exist deja'
        })
    productid=request.GET.get('productid')
    mark=request.GET.get('mark')
    minstock=request.GET.get('minstock')
    product=Produit.objects.get(pk=productid)
    Produit.objects.create(
        ref=ref,
        name=product.name,
        mark_id=mark,
        category=product.category,
        minstock=minstock,
        image=product.image,
        stocktotal=0,
        stockfacture=0,
        buyprice=0,
        netprice=0,
    )
    return JsonResponse({
        'success':True
    })

# ste1=Farah
def ste1(request):
    #initiating config
    
    return render(request, 'fdashboard.html', {'target':'f'})

# ste1=Farah
def ste2(request):
    return render(request, 'odashboard.html', {'target':'o'})

def pointdevente(request):
    return render(request, 'pos.html', {'target':'s'})

def bonsortie(request):
    # get the last order_no
    # if there is no order_no then set it to this format 'ym0001'
    # else increment it by one

    # increment it
    year = timezone.now().strftime("%y")
    latest_receipt = Bonsortie.objects.filter(
        bon_no__startswith=f'BS{year}'
    ).last()
    # latest_receipt = Bonsortie.objects.filter(
    #     bon_no__startswith=f'BS{year}'
    # ).order_by("-bon_no").first()
    if latest_receipt:
        latest_receipt_no = int(latest_receipt.bon_no[-9:])
        receipt_no = f"BS{year}{latest_receipt_no + 1:09}"
    else:
        receipt_no = f"BS{year}000000001"
    print('>>>>>>', Carlogos.objects.all())
    
    return render(request, 'bonsortie.html', {
        'title':'Bon de Sortie',
        'cars':Carlogos.objects.all()
        # 'clients':Client.objects.all(),
        # # 'products':Produit.objects.all(),
        # 'commercials':Represent.objects.all(),
    })


def addbonsortie(request):

    #current_time = datetime.now().strftime('%H:%M:%S')
    clientid=request.POST.get('clientid')
    car=request.POST.get('car')
    remise=request.POST.get('remise')=='true'
    print('>>>', remise)
    #repid=request.POST.get('repid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    orderid=request.POST.get('orderid', None)
    # orderno
    #transport=request.POST.get('transport')
    note=request.POST.get('note')
    payment=request.POST.get('payment') or 0
    print('>>>>>>', products, totalbon, payment)
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    client=Client.objects.get(pk=clientid)
    client.soldtotal=round(float(client.soldtotal)+float(totalbon), 2)
    client.soldbl=round(float(client.soldbl)+float(totalbon), 2)
    client.save()
    if orderid is not None:
        cmnd=Order.objects.get(pk=orderid)
        cmnd.isdelivered=True
        cmnd.save()
    # get the last bon no
    year = timezone.now().strftime("%y")
    latest_receipt = Bonsortie.objects.filter(
        bon_no__startswith=f'BS{year}'
    ).last()
    # latest_receipt = Bonsortie.objects.filter(
    #     bon_no__startswith=f'BS{year}'
    # ).order_by("-bon_no").first()
    if latest_receipt:
        latest_receipt_no = int(latest_receipt.bon_no[-9:])
        receipt_no = f"BS{year}{latest_receipt_no + 1:09}"
    else:
        receipt_no = f"BS{year}000000001"
    order=Bonsortie.objects.create(
        remise=remise,
        client_id=clientid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        user=request.user,
        paidamount=payment,
        car=car
    )
    print('>>>>>>', len(json.loads(products))>0)
    #if len(json.loads(products))>0:
    with transaction.atomic():
        for i in json.loads(products):
            farah=i['farah']=='1'
            product=Produit.objects.get(pk=i['productid'])
            #create sortie items
            sortitem=Sortieitem.objects.create(
                bon=order,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                client_id=clientid,
                date=datebon,
                isfarah=farah,
            )
        
            # update stock accordinly
            if farah:
                product.stocktotalfarah=float(product.stocktotalfarah)-float(i['qty'])
                # negative=json.loads(product.frnegative)
                # sorties=json.loads(product.frsorties)
                # if float(product.stocktotalfarah)-float(i['qty'])<0:
                #     product.isnegativeinfr=True
                #     negative.append(float(i['qty'])-float(product.stocktotalfarah))
                #     sorties.append(sortitem.id)
                #     product.frnegative=negative
                #     product.frsorties=sorties
            
            else:
                negative=json.loads(product.negative)
                sorties=json.loads(product.sorties)
                product.stocktotalorgh=float(product.stocktotalorgh)-float(i['qty'])
                # negative=json.loads(product.negative)
                # sorties=json.loads(product.sorties)
                # if float(product.stocktotalorgh)-float(i['qty'])<0:
                #     product.isnegative=True
                #     negative.append(float(i['qty'])-float(product.stocktotalfarah))
                #     sorties.append(sortitem.id)
                # product.negative=negative
                # product.sorties=sorties
            product.save()
            
            # update prices accordinly
            # pri lli7diffo' d mnchk addifo4n 4kola pri
            # pricesofout=[]
            # qtyofout=[]
            # prices=Stockin.objects.filter(qtyofprice__gt=0, isfarah=farah, product=product, isavoir=False).order_by('id')
            # thisqty=int(i['qty'])
            # for pr in prices:
            #     print('>> qty', thisqty, pr.product.ref)
            #     if not thisqty<=0:
            #         print('>> qty is not 0')
            #         if pr.qtyofprice<=thisqty:
            #             thisqty=thisqty-int(pr.qtyofprice)
            #             qtyofout.append(pr.qtyofprice)
            #             pr.qtyofprice=0
            #             pricesofout.append(pr.id)
            #         else:
            #             pr.qtyofprice=int(pr.qtyofprice)-thisqty
            #             qtyofout.append(thisqty)
            #             thisqty=0
            #             pricesofout.append(pr.id)
            #         pr.save()
            #     else:
            #         print('>> qty', thisqty, pr.product.ref, 'breaking')
            #         break
            # sortitem.pricesofout=pricesofout
            # sortitem.qtyofout=qtyofout
            # sortitem.save()
    # if float(payment)>0:
    #     PaymentClientbl.objects.create(
    #         client_id=clientid,
    #         amount=payment,
    #         date=date.today(),
    #         mode='espece',
    #         npiece=f'Paiement de bon de sortie {order.bon_no}',
    #         issortie=True
    #     )
    if float(payment)>0:
        if remise:
            print('>> Remise')
            order.remise=True
            order.remiseamount=round(float(totalbon)-float(payment), 2)
        order.ispaid=True
        regl=PaymentClientbl.objects.create(
            client_id=clientid,
            amount=payment,
            date=date.today(),
            mode='espece',
            #npiece=f'Paiement de bon de sortie {order.bon_no}',
            npiece=f'espece',
            issortie=True
        )
        regl.bonsortie.set([order])
    
    
    # if float(payment)>0:
    #     if float(payment)==float(totalbon):
    #         print('>> crt regl')
    #         order.ispaid=True
    #         PaymentClientbl.objects.create(
    #             client_id=clientid,
    #             amount=payment,
    #             date=date.today(),
    #             mode='espece',
    #             #npiece=f'Paiement de bon de sortie {order.bon_no}',
    #             npiece=f'espece',
    #             issortie=True
    #         )
    #     else:
    #         if remise:
    #             print('>> Remise')
    #             order.ispaid=True
    #             order.remiseamount=round(float(totalbon)-float(payment), 2)
    #             PaymentClientbl.objects.create(
    #                 client_id=clientid,
    #                 amount=payment,
    #                 date=date.today(),
    #                 mode='espece',
    #                 #npiece=f'Paiement de bon de sortie {order.bon_no}',
    #                 npiece=f'espece',
    #                 issortie=True
    #             )
    #         else:
    #             print('>> crt avance')
    #             order.rest=round(float(totalbon)-float(payment), 2)
    #             Avanceclient.objects.create(
    #                 client_id=clientid,
    #                 amount=payment,
    #                 #today
    #                 date=timezone.now().date(),
    #                 npiece=f'Avance de bon de sortie {order.bon_no}',
    #                 issortie=True
    #             )
    
    order.save()
    client.soldtotal=round(float(client.soldtotal)-float(payment), 2)
    client.soldbl=round(float(client.soldbl)-float(payment), 2)
    client.save()
    # increment it
    return JsonResponse({
        "success":True
    })
# my code
# def validatebonsortie(request):
#     year=timezone.now().year
#     bonid=request.GET.get('blid')
#     bon=Bonsortie.objects.get(pk=bonid)
#     items=Sortieitem.objects.filter(bon=bon)
#     totalfarah=0
#     farahitems=[]
#     totalorgh=0
#     orghitems=[]
#     for i in items:
#         product=i.product
#         if i.isfarah:
#             totalfarah+=float(i['total'])
#             #product.stocktotalfarah=int(product.stocktotalfarah)-int(i.qty)
#             livraisonfarah=Livraisonitem.objects.create(
#                 total=i.total,
#                 qty=i.qty,
#                 product=product,
#                 price=i.price,
#                 client_id=i.client,
#                 date=timezone.now,
#                 isfarah=True
#             )
#             farahitems.append(livraisonfarah)
#         else:
#             totalorgh+=float(i.total)
#             #product.stocktotalorgh=int(product.stocktotalorgh)-int(i.qty)
#             livraisonorgh=Livraisonitem.objects.create(
#                 total=i.total,
#                 qty=i.qty,
#                 product=product,
#                 price=i.price,
#                 client_id=i.client,
#                 date=timezone.now,
#                 isorgh=True
#             )
#             orghitems.append(livraisonorgh)
#         #product.stocktotal=int(product.stocktotal)-int(i['qty'])
#         #product.save()
#     if len(farahitems)>0:
#         latest_receipt = Bonlivraison.objects.filter(
#             bon_no__startswith=f'FR-BL{year}'
#         ).last()
#         # latest_receipt = Bonsortie.objects.filter(
#         #     bon_no__startswith=f'FR-BL{year}'
#         # ).order_by("-bon_no").first()
#         if latest_receipt:
#             latest_receipt_no = int(latest_receipt.bon_no[-9:])
#             receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
#         else:
#             receipt_no = f"FR-BL{year}000000001"
#         # create bon livraison in farah
#         bon=Bonlivraison.objects.create(
#             client_id=bon.client,
#             total=totalfarah,
#             date=timezone.now,
#             bon_no=receipt_no,
#             note=bon.note,
#             isfarah=True
#         )
#         # assign bons
#         for i in farahitems:
#             i.bon=bon
#             i.save()
#     if len(orghitems)>0:
#         latest_receipt = Bonlivraison.objects.filter(
#             bon_no__startswith=f'BL{year}'
#         ).last()
#         # latest_receipt = Bonsortie.objects.filter(
#         #     bon_no__startswith=f'BL{year}'
#         # ).order_by("-bon_no").first()
#         if latest_receipt:
#             latest_receipt_no = int(latest_receipt.bon_no[-9:])
#             receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
#         else:
#             receipt_no = f"BL{year}000000001"
#         # create bon livraison in orgh
#         bon=Bonlivraison.objects.create(
#             client=bon.client,
#             total=totalorgh,
#             date=timezone.now,
#             bon_no=receipt_no,
#             note=bon.note,
#             isorgh=True
#         )
#         # assign bons
#         for i in orghitems:
#             i.bon=bon
#             i.save()
#     return JsonResponse({
#         'succss':True
#     })

#optimized code

def paybonsortie(request):
    bonid = request.GET.get('bonid')
    bon=Bonsortie.objects.get(pk=bonid)
    bon.ispaid=True
    bon.save()
    return JsonResponse({
        'success':True
    })

def validatebonsortie(request):
    year = timezone.now().strftime("%y")
    bonid = request.GET.get('bonid')
    
    bon = Bonsortie.objects.get(pk=bonid)
    bonpaid=bon.ispaid
    items = Sortieitem.objects.filter(bon=bon)
    totalfarah, totalorgh = 0, 0
    farahitems, orghitems = [], []
    
    # Prepare Livraisonitems
    for i in items:
        product = i.product
        item_total = float(i.total)
        
        livraison_data = {
            'total': item_total,
            'qty': i.qty,
            
            'name': i.name,
            'product': product,
            'price': i.price,
            'client': i.client,
            'date': date.today()
        }

        if i.isfarah:
            totalfarah += item_total
            livraison_data['ref']=i.ref.replace('(FR) ', '')
            livraison_data['isfarah'] = True
            farahitems.append(Livraisonitem(**livraison_data))
        else:
            totalorgh += item_total
            livraison_data['ref']=i.ref.replace('(OR) ', '')
            livraison_data['isorgh'] = True
            orghitems.append(Livraisonitem(**livraison_data))
    
    # Helper function to generate Bonlivraison
    def create_bonlivraison(prefix, total, items, is_farah):
        latest_receipt = Bonlivraison.objects.filter(
            bon_no__startswith=f'{prefix}{year}'
        ).last()
        
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"{prefix}{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"{prefix}{year}000000001"
        
        bon_data = {
            'total': total,
            'date': date.today(),
            'bon_no': receipt_no,
            'note': bon.note,
            'bonsortie':bon,
            # make created bon paid if the original bon is paid
            #'ispaid':bonpaid
        }
        
        if is_farah:
            bon_data['isfarah'] = True
            # the client of the bon created will always be the first client
            bon_data['client'] = Client.objects.get(code='CF-1')
        else:
            bon_data['isorgh'] = True
            bon_data['client'] = Client.objects.get(code='CO-1')
        
        new_bon = Bonlivraison.objects.create(**bon_data)
        
        for item in items:
            item.bon = new_bon
            item.save()
    
    # Create Bonlivraison for farah items
    if farahitems:
        create_bonlivraison('FR-BL', totalfarah, farahitems, is_farah=True)
    
    # Create Bonlivraison for orgh items
    if orghitems:
        create_bonlivraison('BL', totalorgh, orghitems, is_farah=False)
    bon.generated=True
    bon.save()
    return JsonResponse({'success': True})

def validatebonsortieproductprice(request):
    year = timezone.now().strftime("%y")
    bonid = request.GET.get('bonid')
    
    bon = Bonsortie.objects.get(pk=bonid)
    
    items = Sortieitem.objects.filter(bon=bon)
    totalfarah, totalorgh = 0, 0
    farahitems, orghitems = [], []
    
    # Prepare Livraisonitems
    for i in items:
        product = i.product
        item_total = float(i.total)
        # cou moyen
        prices=Stockin.objects.filter(pk__in=json.loads(i.pricesofout))
        qtyofout=json.loads(i.qtyofout)
        print('>> price hist', prices, i.pricesofout)
        p=round(i.price/0.75, 2)
        pbrut=i.price
        print('>>> price before', p, i.price)
        if prices:
            allprices=0
            for pr, qty in zip(prices, qtyofout):
                allprices+=pr.net*qty
            p=round(allprices/sum(qtyofout), 2)
            p=round(p/0.65, 2)
            #p=round(p-(p*0.25), 2)
        print('>>>> price', p)

        livraison_data = {
            'pricesofout':i.pricesofout,
            'qtyofout':i.qtyofout,
            'total': round(round(p-(p*0.25), 2)*i.qty, 2),
            'price':p,
            'remise':25,
            'qty': i.qty,
            'name': i.name,
            'product': product,
            'client': i.client,
            'date': date.today()
        }

        if i.isfarah:
            totalfarah += round(round(p-(p*0.25), 2)*i.qty, 2)
            livraison_data['ref']=i.ref.replace('(FR) ', '')
            livraison_data['isfarah'] = True
            #livraison_data['price'] = product.frsellprice
            farahitems.append(Livraisonitem(**livraison_data))
        else:
            totalorgh += round(round(p-(p*0.25), 2)*i.qty, 2)
            livraison_data['ref']=i.ref.replace('(OR) ', '')
            livraison_data['isorgh'] = True
            #livraison_data['price'] = product.sellprice
            orghitems.append(Livraisonitem(**livraison_data))
    
    # Helper function to generate Bonlivraison
    def create_bonlivraison(prefix, total, items, is_farah):
        latest_receipt = Bonlivraison.objects.filter(
            bon_no__startswith=f'{prefix}{year}'
        ).last()
        
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"{prefix}{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"{prefix}{year}000000001"
        
        bon_data = {
            'total': round(total, 2),
            'date': timezone.now(),
            'bon_no': receipt_no,
            'note': bon.note,
            'bonsortie':bon,
            'note':f'{bon.car}-{bon.note}'
            # make created bon paid if the original bon is paid
            #'ispaid':bonpaid
        }
        
        if is_farah:
            bon_data['isfarah'] = True
            # the client of the bon created will always be the first client
            bon_data['client'] = Client.objects.get(code='CF-1')
        else:
            bon_data['isorgh'] = True
            bon_data['client'] = Client.objects.get(code='CO-1')
        
        new_bon = Bonlivraison.objects.create(**bon_data)
        
        for item in items:
            item.bon = new_bon
            item.save()
    
    # Create Bonlivraison for farah items
    if farahitems:
        create_bonlivraison('FR-BL', totalfarah, farahitems, is_farah=True)
    
    # Create Bonlivraison for orgh items
    if orghitems:
        create_bonlivraison('BL', totalorgh, orghitems, is_farah=False)
    bon.generated=True
    bon.save()
    return JsonResponse({'success': True})

def farahhome(request):
    return render(request, 'farahhome.html', {'target':'f'})

def orghhome(request):
    return render(request, 'orghhome.html', {'target':'o'})

def clientsection(request):
    target=request.GET.get('target')
    print('>> terget', target)
    print('faracl', Client.objects.filter(clientfarah=True).count())
    if target=='s':
        try:
            lastcode = Client.objects.filter(code__startswith='CP-').last()
            print('lastcode', lastcode.code)
            if lastcode:
                codecl = f"CP-{int(lastcode.code.split('-')[1]) + 1}"
            else:
                codecl = f"CP-1"
        except:
            codecl="CP-1"
        clients=Client.objects.filter(clientsortie=True).order_by('-soldtotal')[:50]
    elif target=='f':
        try:
            lastcode = Client.objects.filter(code__startswith='CF').last()
            print('lastcode', lastcode.code)
            if lastcode:

                codecl = f"CF-{int(lastcode.code.split('-')[1]) + 1}"
            else:
                codecl = f"CF-1"
        except:
            codecl="CF-1"
        clients=Client.objects.filter(clientfarah=True).order_by('-soldtotal')[:50]
    else:
        try:
            lastcode = Client.objects.filter(code__startswith='CO').last()
            print('lastcode', lastcode.code)
            if lastcode:

                codecl = f"CO-{int(lastcode.code.split('-')[1]) + 1}"
            else:
                codecl = f"CO-1"
        except:
            codecl="CO-1"
        clients=Client.objects.filter(clientorgh=True).order_by('-soldtotal')[:50]
    
    ctx={
        'clients':clients,
        'title':'List des clients',
        'lastcode':codecl,
        'target':target
        # 'sortiesection':sortie,
        # 'farahsection':farah,
        # 'orghsection':orgh,
        # 'soldtotal':round(Client.objects.aggregate(Sum('soldtotal'))['soldtotal__sum'] or 0, 2),
        # 'soldbl':round(Client.objects.aggregate(Sum('soldbl'))['soldbl__sum'] or 0, 2),
        # 'soldfacture':round(Client.objects.aggregate(Sum('soldfacture'))['soldfacture__sum'] or 0, 2),
    }
    return render(request, 'clientsection.html', ctx)

def ventesection(request):
    target=request.GET.get('target')
    today = timezone.now().date()
    thisyear=timezone.now().year
    current_time = datetime.now().strftime('%H:%M:%S')
    three_months_ago = timezone.now() - timedelta(days=90)  # Assuming 30 days per month on average

    # Query for Bonlivraison objects that have a 'date' field earlier than three months ago
    #depasser = Bonlivraison.objects.filter(date__lt=three_months_ago, ispaid=False, total__gt=0).count()
    # get only the last 100 orders of the current year
    # only check one target as bon livraison is only for farah or orgh, pos has bonsortie
    if target=='f':
        bons= Bonlivraison.objects.filter(isfarah=True, date__year=timezone.now().year).order_by('-bon_no')[:50]
        total=Bonlivraison.objects.filter(isfarah=True, date__year=timezone.now().year).aggregate(Sum('total')).get('total__sum')
    else:
        bons= Bonlivraison.objects.filter(isorgh=True, date__year=timezone.now().year).order_by('-bon_no')[:50]
        total=Bonlivraison.objects.filter(isorgh=True, date__year=timezone.now().year).aggregate(Sum('total')).get('total__sum')
    ctx={
        'title':'Bons de livraison',
        'bons':bons,
        'total':total,
        #'boncommand':Order.objects.filter(isdelivered=False).exclude(note__icontains='Reliquat').count(),
        #'depasser':depasser,
        #'reps':Represent.objects.all(),
        'today':timezone.now().date(),
        'target':target
    }
    return render(request, 'ventesection.html', ctx)


def achatsection(request):
    target=request.GET.get('target')
    thisyear=timezone.now().year
    if target=='f':
        bons=Itemsbysupplier.objects.filter(date__year=thisyear, isfarah=True).order_by('-date')[:50]
    elif target=='o':
        bons=Itemsbysupplier.objects.filter(date__year=thisyear, isorgh=True).order_by('-date')[:50]
    ctx={
        'title':'List des bon achat',
        'bons':bons,
        'target':target
    }
    if bons:
        ctx['total']=round(Itemsbysupplier.objects.all().aggregate(Sum('total'))['total__sum'], 2)
        ctx['totaltva']=round(Itemsbysupplier.objects.all().aggregate(Sum('tva'))['tva__sum'], 2)
    return render(request, 'achatsection.html', ctx)

def listbonsortie(request):
    bons=Bonsortie.objects.all().order_by('-bon_no')[:50]
    ctx={
        'title':'List des bons de sortie',
        'bons':bons
    }
    return render(request, 'listbonsortie.html', ctx)

def suppliersection(request):
    target=request.GET.get('target')
    suppliers=Supplier.objects.all()
    ctx={
        'title':'List des fournisseurs',
        'suppliers':suppliers,
        'target':target,
    }
    return render(request, 'suppliersection.html', ctx)

def bonsortiedetails(request, id):
    order=Bonsortie.objects.get(pk=id)
    orderitems=Sortieitem.objects.filter(bon=order).order_by('product__name')
    print('orderitems', orderitems)
    #reglements=PaymentClientbl.objects.filter(bons__in=[order])
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+34] for i in range(0, len(orderitems), 34)]
    reglements=PaymentClientbl.objects.filter(bonsortie__in=[order])
    cars=Carlogos.objects.all()
    ctx={
        'reglements':reglements,
        'title':f'Bon de livraison {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'bonsortie':True,
        'cars':cars
    }
    return render(request, 'bonsortiedetails.html', ctx)



def checkplafon(request):
    clientid=request.GET.get('clientid')
    client=Client.objects.get(pk=clientid)
    plafon=client.plafon
    soldtotal=client.soldtotal
    return JsonResponse({
        'plafon':plafon,
        'soldtotal':soldtotal
    })

def getclientpricesortie(request):
    pdctid=request.POST.get('id')
    clientid=request.POST.get('clientid')
    target=request.POST.get('target')
    term=request.POST.get('term')
    product=Produit.objects.get(pk=pdctid)
    frbuyprice=product.frbuyprice or 0
    frremise=product.frremise1 or 0
    buyprice=product.buyprice or 0
    remiseofbuyorice=product.remise1 or 0
    price=0
    remise=0
    print(frbuyprice, frremise, buyprice, remiseofbuyorice, '>>>', target)
    # buyprice=product.frbuyprice if 'fr' in term else product.buyprice
    # remisebuyprice=product.frremise1 if 'fr' in term else product.remise1
    try:
            clientprice=Sortieitem.objects.filter(client_id=clientid, product_id=pdctid).last()
            price=clientprice.price
            remise=clientprice.remise
            return JsonResponse({
                'price':price,
                'remise':remise,
                'frbuyprice':frbuyprice,
                'frremise':frremise,
                'orbuyprice':buyprice,
                'orremise':remiseofbuyorice,
            })
    except:
        return JsonResponse({
            'price':0,
            'remise':0,
            'frbuyprice':frbuyprice,
            'frremise':frremise,
            'orbuyprice':buyprice,
            'orremise':remiseofbuyorice,
        })
    #if target=='bl':
    #    try:
    #        clientprice=Livraisonitem.objects.filter(client_id=clientid, product_id=id).last()
    #        price=clientprice.price
    #        remise=clientprice.remise
    #        return JsonResponse({
    #            'price':price,
    #            'remise':remise
    #        })
    #    except:
    #        return JsonResponse({
    #            'price':0
    #        })
    #else:
    #    try:
    #        clientprice=Outfacture.objects.filter(client_id=clientid, product_id=id).last()
    #        price=clientprice.price
    #        remise=clientprice.remise
    #        return JsonResponse({
    #            'price':price,
    #            'remise':remise
    #        })
    #    except:
    #        return JsonResponse({
    #            'price':0
    #        })

def addmark(request):
    name=request.POST.get('marque')
    if Mark.objects.filter(name=name).exists():
        return JsonResponse({
            'exist':True,
            'error':'deja exist'
        })
    m=Mark.objects.create(name=name)
    return JsonResponse({
        'success':True,
        'id':m.id,
        'name':name
    })


def addcategory(request):
    name=request.POST.get('category')
    if Category.objects.filter(name=name).exists():
        return JsonResponse({
            'exist':True,
            'error':'deja exist'
        })
    m=Category.objects.create(name=name)
    return JsonResponse({
        'success':True,
        'id':m.id,
        'name':name
    })

def listdevi(request):
    target=request.GET.get('target')
    suppliersection=request.GET.get('suppliersection')=='1'
    if target=='f':
        if suppliersection:
            bons=Devi.objects.filter(isfarah=True, forsupplier=True).order_by('-bon_no')[:50]
        else:
            bons=Devi.objects.filter(isfarah=True).order_by('-bon_no')[:50]
    else:
        if suppliersection:
            bons=Devi.objects.filter(isorgh=True, forsupplier=True).order_by('-bon_no')[:50]
        else:
            bons=Devi.objects.filter(isorgh=True).order_by('-bon_no')[:50]
    ctx={
        'title':'Devi',
        'bons':bons,
        'target':target,
        'suppliersection':suppliersection
    }
    return render(request, 'listdevi.html', ctx)
def bondevi(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Bon de Devi',
        'target':target
    }
    return render(request, 'bondevi.html', ctx)
def boncommand(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Bon de Commande',
        'target':target
    }
    return render(request, 'boncommand.html', ctx)
def devitoboncommand(request):
    target=request.GET.get('target')
    devid=request.GET.get('devid')
    order=Devi.objects.get(pk=devid)
    items=DeviItem.objects.filter(devi=order)
    client=order.client
    ctx={
        'order':order,
        'items':items,
        #'receipt_no':receipt_no,
        #'clients':Client.objects.all(),
        'today':timezone.now().date(),
        'devi':True,
        'target':target
    }

    return render(request, 'devitoboncommand.html', ctx)
def createdevi(request):
    target=request.POST.get('target')
    isfarah=False
    isorgh=False
    if target=='f':
        isfarah=True
        year = timezone.now().strftime("%y")
        latest_receipt = Devi.objects.filter(
            bon_no__startswith=f'FR-DV{year}'
        ).last()
        # latest_receipt = Devi.objects.filter(
        #     bon_no__startswith=f'FR-DV{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FR-DV{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-DV{year}000000001"
    else:
        isorgh=True
        year = timezone.now().strftime("%y")
        latest_receipt = Devi.objects.filter(
            bon_no__startswith=f'DV{year}'
        ).last()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"DV{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"DV{year}000000001"
    clientid=request.POST.get('clientid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    orderid=request.POST.get('orderid', None)
    # orderno
    transport=request.POST.get('transport')
    note=request.POST.get('note')
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    
    # if orderid is not None:
    #     cmnd=Order.objects.get(pk=orderid)
    #     cmnd.isdelivered=True
    #     cmnd.save()
    # get the last bon no
    
    order=Devi.objects.create(
        client_id=clientid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        isfarah=isfarah,
        isorgh=isorgh,
        user=request.user
    )
    # if len(json.loads(products))>0:
    with transaction.atomic():
        for i in json.loads(products):
            product=Produit.objects.get(pk=i['productid'])
            
            DeviItem.objects.create(
                devi=order,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                client_id=clientid,
                date=datebon,
                isfarah=isfarah,
                isorgh=isorgh
            )


    # increment it
    return JsonResponse({
        "success":True
    })
def createboncommand(request):
    target=request.POST.get('target')
    devid=request.POST.get('devid')
    isfarah=False
    isorgh=False
    if target=='f':
        isfarah=True
        year = timezone.now().strftime("%y")
        latest_receipt = Command.objects.filter(
            bon_no__startswith=f'FR-BC{year}'
        ).last()
        # latest_receipt = Devi.objects.filter(
        #     bon_no__startswith=f'FR-BC{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FR-BC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-BC{year}000000001"
    else:
        isorgh=True
        year = timezone.now().strftime("%y")
        latest_receipt = Command.objects.filter(
            bon_no__startswith=f'BC{year}'
        ).last()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"BC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"BC{year}000000001"
    clientid=request.POST.get('clientid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    note=request.POST.get('note')
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    print('>>> datebon', datebon, 'target', target, 'isfarah', isfarah, 'isorgh', isorgh, 'clientid', clientid, 'products', products, 'totalbon', totalbon, 'note', note, 'devid', devid, 'receipt_no', receipt_no, 'user', request.user)
    # if orderid is not None:
    #     cmnd=Order.objects.get(pk=orderid)
    #     cmnd.isdelivered=True
    #     cmnd.save()
    # get the last bon no
    
    order=Command.objects.create(
        client_id=clientid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        isfarah=isfarah,
        isorgh=isorgh,
        user=request.user
    )
    if not devid == "":
        devi=Devi.objects.get(pk=devid)
        devi.generatedbc=True
        devi.bc=order
        devi.save()
        order.devi=devi
        order.save()
    # if len(json.loads(products))>0:
    with transaction.atomic():
        for i in json.loads(products):
            product=Produit.objects.get(pk=i['productid'])
            
            CommandItem.objects.create(
                command=order,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                client_id=clientid,
                date=datebon,
                isfarah=isfarah,
                isorgh=isorgh
            )


    # increment it
    return JsonResponse({
        "success":True
    })
def devidetails(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    order=Devi.objects.get(pk=id)
    orderitems=DeviItem.objects.filter(devi=order).order_by('product__name')
    #reglements=PaymentClientbl.objects.filter(bons__in=[order])
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+34] for i in range(0, len(orderitems), 34)]
    ctx={
        'title':f'Devi {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'target':target
        
    }
    return render(request, 'devidetails.html', ctx)
def boncommanddetails(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    order=Command.objects.get(pk=id)
    orderitems=CommandItem.objects.filter(command=order).order_by('product__name')
    #reglements=PaymentClientbl.objects.filter(bons__in=[order])
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+34] for i in range(0, len(orderitems), 34)]
    ctx={
        'title':f'Bonc commande {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'target':target
        
    }
    return render(request, 'boncommanddetails.html', ctx)
def boncommandobl(request):
    target=request.GET.get('target')
    commandid=request.GET.get('commandid')
    command=Command.objects.get(pk=commandid)
    items=CommandItem.objects.filter(command=command)
    client=command.client
    ctx={
        'command':command,
        'items':items,
        'sold':client.soldtotal,
        #'receipt_no':receipt_no,
        #'clients':Client.objects.all(),
        'today':timezone.now().date(),
        'target':target
    }

    return render(request, 'genererbonlivraison.html', ctx)
    # print('>>> target', target)
    # if target=='f':
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'FR-BL{year}'
    #     ).last()
    #     # latest_receipt = Bonsortie.objects.filter(
    #     #     bon_no__startswith=f'FR-BL{year}'
    #     # ).order_by("-bon_no").first()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"FR-BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isfarah=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalfarah=float(product.stocktotalfarah)-float(i.qty)
    #         product.save()
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isfarah=True
    #         )

    # else:
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'BL{year}'
    #     ).last()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isorgh=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalorgh=float(product.stocktotalorgh)-float(i.qty)
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=i.product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isorgh=True
    #         )
    # devi.generatedbl=True
    # devi.save()
    # return JsonResponse({
    #     'success':True
    # })
def devitobl(request):
    target=request.GET.get('target')
    devid=request.GET.get('devid')
    order=Devi.objects.get(pk=devid)
    items=DeviItem.objects.filter(devi=order)
    client=order.client
    ctx={
        'order':order,
        'items':items,
        'sold':client.soldtotal,
        #'receipt_no':receipt_no,
        #'clients':Client.objects.all(),
        'today':timezone.now().date(),
        'devi':True,
        'target':target
    }

    return render(request, 'genererbonlivraison.html', ctx)
    # print('>>> target', target)
    # if target=='f':
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'FR-BL{year}'
    #     ).last()
    #     # latest_receipt = Bonsortie.objects.filter(
    #     #     bon_no__startswith=f'FR-BL{year}'
    #     # ).order_by("-bon_no").first()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"FR-BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isfarah=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalfarah=float(product.stocktotalfarah)-float(i.qty)
    #         product.save()
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isfarah=True
    #         )

    # else:
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'BL{year}'
    #     ).last()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isorgh=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalorgh=float(product.stocktotalorgh)-float(i.qty)
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=i.product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isorgh=True
    #         )
    # devi.generatedbl=True
    # devi.save()
    # return JsonResponse({
    #     'success':True
    # })
def listcommand(request):
    isfarah=request.GET.get('target')=='f'
    bons=Command.objects.filter(isfarah=isfarah).order_by('-bon_no')[:50]
    ctx={
        'title':'List des commandes',
        'bons':bons,
        'target':request.GET.get('target')
    }
    return render(request, 'listcommand.html', ctx)
        
def supplierlistdevi(request):
    target=request.GET.get('target')
    if target=='f':
        bons=Devisupplier.objects.filter(isfarah=True).order_by('-bon_no')[:50]
    else:
        bons=Devisupplier.objects.filter(isorgh=True).order_by('-bon_no')[:50]
    ctx={
        'title':'Devi',
        'bons':bons,
        'target':target,
    }
    return render(request, 'listdevisupplier.html', ctx)
def supplierbondevi(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Bon de Devi',
        'target':target
    }
    return render(request, 'supplierbondevi.html', ctx)
def supplierboncommand(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Bon de Commande',
        'target':target
    }
    return render(request, 'supplierboncommand.html', ctx)
def supplierdevitoboncommand(request):
    target=request.GET.get('target')
    devid=request.GET.get('devid')
    order=Devisupplier.objects.get(pk=devid)
    items=DeviItemsupplier.objects.filter(devi=order)
    supplier=order.supplier
    ctx={
        'order':order,
        'items':items,
        # 'sold':supplier.soldtotal,
        #'receipt_no':receipt_no,
        #'clients':Client.objects.all(),
        'today':timezone.now().date(),
        'devi':True,
        'target':target
    }

    return render(request, 'supplierdevitoboncommand.html', ctx)
def suppliercreatedevi(request):
    target=request.POST.get('target')
    isfarah=False
    isorgh=False
    if target=='f':
        isfarah=True
        year = timezone.now().strftime("%y")
        latest_receipt = Devisupplier.objects.filter(
            bon_no__startswith=f'FR-FDV{year}'
        ).last()
        # latest_receipt = Devi.objects.filter(
        #     bon_no__startswith=f'FR-DV{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FR-FDV{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-FDV{year}000000001"
    else:
        isorgh=True
        year = timezone.now().strftime("%y")
        latest_receipt = Devisupplier.objects.filter(
            bon_no__startswith=f'FDV{year}'
        ).last()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FDV{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FDV{year}000000001"
    supplierid=request.POST.get('supplierid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    orderid=request.POST.get('orderid', None)
    # orderno
    transport=request.POST.get('transport')
    note=request.POST.get('note')
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    
    # if orderid is not None:
    #     cmnd=Order.objects.get(pk=orderid)
    #     cmnd.isdelivered=True
    #     cmnd.save()
    # get the last bon no
    
    order=Devisupplier.objects.create(
        supplier_id=supplierid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        isfarah=isfarah,
        isorgh=isorgh,
        user=request.user
    )
    # if len(json.loads(products))>0:
    with transaction.atomic():
        for i in json.loads(products):
            product=Produit.objects.get(pk=i['productid'])
            
            DeviItemsupplier.objects.create(
                devi=order,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                supplier_id=supplierid,
                date=datebon,
                isfarah=isfarah,
                isorgh=isorgh
            )


    # increment it
    return JsonResponse({
        "success":True
    })
def suppliercreateboncommand(request):
    target=request.POST.get('target')
    devid=request.POST.get('devid')
    isfarah=False
    isorgh=False
    if target=='f':
        isfarah=True
        year = timezone.now().strftime("%y")
        latest_receipt = Commandsupplier.objects.filter(
            bon_no__startswith=f'FR-FBC{year}'
        ).last()
        # latest_receipt = Devi.objects.filter(
        #     bon_no__startswith=f'FR-BC{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FR-FBC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-FBC{year}000000001"
    else:
        isorgh=True
        year = timezone.now().strftime("%y")
        latest_receipt = Commandsupplier.objects.filter(
            bon_no__startswith=f'FBC{year}'
        ).last()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.bon_no[-9:])
            receipt_no = f"FBC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FBC{year}000000001"
    supplierid=request.POST.get('supplierid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    note=request.POST.get('note')
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    print('target', target, 'isfarah', isfarah, 'isorgh', isorgh, 'receipt_no', receipt_no, 'supplierid', supplierid, 'products', products, 'totalbon', totalbon, 'note', note, 'datebon', datebon, 'devid', devid)
    # if orderid is not None:
    #     cmnd=Order.objects.get(pk=orderid)
    #     cmnd.isdelivered=True
    #     cmnd.save()
    # get the last bon no
    
    order=Commandsupplier.objects.create(
        supplier_id=supplierid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        isfarah=isfarah,
        isorgh=isorgh,
        user=request.user
    )
    if not devid == '':
        devi=Devisupplier.objects.get(pk=devid)
        devi.generatedbc=True
        devi.bc=order
        order.devi=devi
        order.save()
        devi.save()
    # if len(json.loads(products))>0:
    with transaction.atomic():
        for i in json.loads(products):
            product=Produit.objects.get(pk=i['productid'])
            
            CommandItemsupplier.objects.create(
                command=order,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                supplier_id=supplierid,
                date=datebon,
                isfarah=isfarah,
                isorgh=isorgh
            )


    # increment it
    return JsonResponse({
        "success":True
    })
def supplierdevidetails(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    order=Devisupplier.objects.get(pk=id)
    orderitems=DeviItemsupplier.objects.filter(devi=order).order_by('product__name')
    #reglements=PaymentClientbl.objects.filter(bons__in=[order])
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+34] for i in range(0, len(orderitems), 34)]
    ctx={
        'title':f'Devi {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'target':target
        
    }
    return render(request, 'supplierdevidetails.html', ctx)
def supplierboncommanddetails(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    order=Commandsupplier.objects.get(pk=id)
    orderitems=CommandItemsupplier.objects.filter(command=order).order_by('product__name')
    #reglements=PaymentCliséentbl.objects.filter(bons__in=[order])
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+34] for i in range(0, len(orderitems), 34)]
    ctx={
        'title':f'Bonc commande {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'target':target
        
    }
    return render(request, 'supplierboncommanddetails.html', ctx)
def supplierboncommandobl(request):
    target=request.GET.get('target')
    commandid=request.GET.get('commandid')
    command=Commandsupplier.objects.get(pk=commandid)
    items=CommandItemsupplier.objects.filter(command=command)
    supplier=command.supplier
    ctx={
        'cmnd':command,
        'items':items,
        'sold':supplier.rest,
        #'receipt_no':receipt_no,
        #'suppliers':supplier.objects.all(),
        'today':timezone.now().date(),
        'target':target
    }

    return render(request, 'genererbonachat.html', ctx)
    # print('>>> target', target)
    # if target=='f':
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'FR-BL{year}'
    #     ).last()
    #     # latest_receipt = Bonsortie.objects.filter(
    #     #     bon_no__startswith=f'FR-BL{year}'
    #     # ).order_by("-bon_no").first()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"FR-BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isfarah=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalfarah=float(product.stocktotalfarah)-float(i.qty)
    #         product.save()
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isfarah=True
    #         )

    # else:
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'BL{year}'
    #     ).last()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isorgh=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalorgh=float(product.stocktotalorgh)-float(i.qty)
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=i.product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isorgh=True
    #         )
    # devi.generatedbl=True
    # devi.save()
    # return JsonResponse({
    #     'success':True
    # })
def supplierdevitobl(request):
    target=request.GET.get('target')
    devid=request.GET.get('devid')
    order=Devisupplier.objects.get(pk=devid)
    items=DeviItemsupplier.objects.filter(devi=order)
    supplier=order.supplier
    ctx={
        'devi':order,
        'items':items,
        'sold':supplier.rest,
        #'receipt_no':receipt_no,
        #'clients':Client.objects.all(),
        'today':timezone.now().date(),
        'target':target
    }

    return render(request, 'genererbonachat.html', ctx)
    # print('>>> target', target)
    # if target=='f':
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'FR-BL{year}'
    #     ).last()
    #     # latest_receipt = Bonsortie.objects.filter(
    #     #     bon_no__startswith=f'FR-BL{year}'
    #     # ).order_by("-bon_no").first()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"FR-BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isfarah=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalfarah=float(product.stocktotalfarah)-float(i.qty)
    #         product.save()
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isfarah=True
    #         )

    # else:
    #     year = timezone.now().strftime("%y")
    #     latest_receipt = Bonlivraison.objects.filter(
    #         bon_no__startswith=f'BL{year}'
    #     ).last()
    #     if latest_receipt:
    #         latest_receipt_no = int(latest_receipt.bon_no[-9:])
    #         receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
    #     else:
    #         receipt_no = f"BL{year}000000001"
    #     bon=Bonlivraison.objects.create(
    #         client_id=devi.client_id,
    #         total=devi.total,
    #         date=date.today(),
    #         bon_no=receipt_no,
    #         note=devi.note,
    #         isorgh=True
    #     )   
    #     for i in items:
    #         product=i.product
    #         product.stocktotalorgh=float(product.stocktotalorgh)-float(i.qty)
    #         Livraisonitem.objects.create(
    #             bon=bon,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=i.product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=devi.client_id,
    #             date=date.today(),
    #             isorgh=True
    #         )
    # devi.generatedbl=True
    # devi.save()
    # return JsonResponse({
    #     'success':True
    # })
def supplierlistcommand(request):
    isfarah=request.GET.get('target')=='f'
    bons=Commandsupplier.objects.filter(isfarah=isfarah).order_by('-bon_no')[:50]
    ctx={
        'title':'List des commandes',
        'bons':bons,
        'target':request.GET.get('target')
    }
    return render(request, 'supplierlistcommand.html', ctx)
 
def getclientbonsforfacture(request):
    clientid=request.POST.get('clientid')
    target=request.POST.get('target')
    print('>> target', target)
    if target=='s':
        bons=Bonsortie.objects.filter(client_id=clientid, isfacture=False).order_by('date')
        total=round(Bonsortie.objects.filter(client_id=clientid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    elif target=='f':
        bons=Bonlivraison.objects.filter(client_id=clientid, isfacture=False, isfarah=True).order_by('date')[:50]
        total=round(Bonlivraison.objects.filter(client_id=clientid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    else:
        bons=Bonlivraison.objects.filter(client_id=clientid, isfacture=False, isfarah=False).order_by('date')[:50]
        total=round(Bonlivraison.objects.filter(client_id=clientid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    trs=''
    for i in bons:
        # old code, if reglement is paid it's checked from here
        # trs+=f'<tr style="background: {"rgb(221, 250, 237);" if i.reglements.exists() else ""}" class="blreglrow" clientid="{clientid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.client.name}</td><td>{i.total}</td><td class="text-danger">{"RR" if i.reglements.exists() else "NR"}</td> <td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)" {"checked" if i.reglements.exists() else ""}></td></tr>'
        trs+=f'<tr class="blreglrow" clientid="{clientid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.client.name}</td><td>{i.total} {"(Reglé)" if i.ispaid else ""}</td><td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)"></td></tr>'


    return JsonResponse({
        'trs':trs,
        'total':total,
        'soldbl':round(Client.objects.get(pk=clientid).soldbl, 2)
    })


def getsupplierbonsforfacture(request):
    supplierid=request.POST.get('supplierid')
    target=request.POST.get('target')
    print('>> target', target)
    if target=='f':
        bons=Itemsbysupplier.objects.filter(supplier_id=supplierid, isfacture=False, isfarah=True)
        total=round(Itemsbysupplier.objects.filter(supplier_id=supplierid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    else:
        bons=Bonlivraison.objects.filter(supplier_id=supplierid, isfacture=False, isfarah=False)
        total=round(Bonlivraison.objects.filter(supplier_id=supplierid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    trs=''
    for i in bons:
        # old code, if reglement is paid it's checked from here
        # trs+=f'<tr style="background: {"rgb(221, 250, 237);" if i.reglements.exists() else ""}" class="blreglrow" clientid="{clientid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.client.name}</td><td>{i.total}</td><td class="text-danger">{"RR" if i.reglements.exists() else "NR"}</td> <td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)" {"checked" if i.reglements.exists() else ""}></td></tr>'
        trs+=f'<tr class="blreglrow" supplierid="{supplierid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.nbon}{"(reglé)" if i.ispaid else ""}</td><td>{i.supplier.name}</td><td>{i.total}</td><td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)"></td></tr>'


    return JsonResponse({
        'trs':trs,
        'total':total,
        'soldbl':round(Supplier.objects.get(pk=supplierid).rest, 2)
    })



def facturemultiple(request):
    # create  facture with multiple bons
    date=request.GET.get('date')
    date=datetime.strptime(date, '%Y-%m-%d')
    clientid=request.GET.get('clientid')
    target=request.GET.get('target')
    client=Client.objects.get(pk=clientid)
    bons=json.loads(request.GET.get('bons'))
    year=timezone.now().strftime("%y")
    livraisons=Bonlivraison.objects.filter(pk__in=bons)
    livraison_ids = livraisons.values_list('id', flat=True)
    print('>>> bons, livraions',bons, livraisons)
    reglements=PaymentClientbl.objects.filter(bons__in=livraison_ids)
    reglements.update(client_id=clientid)
    livraisons.update(client_id=clientid)
    # check if all bons are paid
    allpaid = all(livraison.ispaid for livraison in livraisons)


    isfarah=False

    if target=='f':
        isfarah=True
        latest_receipt = Facture.objects.filter(
            facture_no__startswith=f'FR-FC{year}'
        ).last()
        # latest_receipt = Bonsortie.objects.filter(
        #     facture_no__startswith=f'FR-BL{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.facture_no[-9:])
            receipt_no = f"FR-FC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-FC{year}000000001"
    else:
        latest_receipt = Facture.objects.filter(
            facture_no__startswith=f'FC{year}'
        ).last()
        # latest_receipt = Bonsortie.objects.filter(
        #     facture_no__startswith=f'FR-BL{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.facture_no[-9:])
            receipt_no = f"FC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FC{year}000000001"
    
    # fc_no=request.GET.get('factureno')
    # # check iffacture with numlber already exist
    # if not fc_no=='':
    #     receipt_no=fc_no
    # facture=Facture.objects.filter(facture_no=fc_no).first()
    # if facture and facture.bons.exists():
    #     return JsonResponse({
    #         'success':False,
    #         'error':'Numero deja exist'
    #     })
    # if facture:
    #     facture=facture
    # else:
    facture=Facture.objects.create(
        facture_no=receipt_no,
        client_id=clientid,
        isfarah=isfarah,
        date=date
    )

    total=0
    
    if allpaid:
        print('>> all bons are paid')
        facture.ispaid=True
        facture.rest=0
    else:
        unpaid_bons = livraisons.filter(ispaid=False)

        # Get the total amount for unpaid bons
        total_unpaid = unpaid_bons.aggregate(total=Sum('total'))['total']
        print('>> not all bons are paid²', total_unpaid)
        facture.rest=total_unpaid
    facture.save()
    # if we have just one bon
    # if len(livraisons)==1:
    #     print(">> here")
    #     bon=livraisons[0]
    #     bon.facture=facture
    #     facture.total=livraisons[0].total
    #     facture.bon=bon
    #     bon.isfacture=True
    #     bon.save()
    #     #get items of bon
    #     items=Livraisonitem.objects.filter(bon=bon)
    #     # create facture items
    #     for i in items:
    #         Outfacture.objects.create(
    #             facture=facture,
    #             remise=i.remise,
    #             name=i.name,
    #             ref=i.ref,
    #             product=i.product,
    #             qty=i.qty,
    #             price=i.price,
    #             total=i.total,
    #             client_id=clientid,
    #             date=date,
    #             isfarah=isfarah
    #         )
    #     # sold facture
    #     client.soldfacture+=bon.total
    # else:
        # iterate throu bons
    for bon in livraisons:
        total+=bon.total
        bon.isfacture=True
        bon.facture=facture
        bon.save()
        # loop items of bon
        items=Livraisonitem.objects.filter(bon=bon)
        # for i in items:
        #     Outfacture.objects.create(
        #         facture=facture,
        #         remise=i.remise,
        #         name=i.name,
        #         ref=i.ref,
        #         product=i.product,
        #         qty=i.qty,
        #         price=i.price,
        #         total=i.total,
        #         client_id=clientid,
        #         date=date,
        #         isfarah=isfarah,
        #         livraison=i
        #     )    
    facture.total=total
    facture.bons.set(livraisons)
    client.soldfacture+=total
    facture.save()
    client.save()
    return JsonResponse({
        'success':True
    })

def factureachatmultiple(request):
    # create  facture with multiple bons
    date=request.GET.get('date')
    date=datetime.strptime(date, '%Y-%m-%d')
    supplierid=request.GET.get('supplierid')
    target=request.GET.get('target')
    supplier=Supplier.objects.get(pk=supplierid)
    bons=json.loads(request.GET.get('bons'))
    year=timezone.now().strftime("%y")
    livraisons=Itemsbysupplier.objects.filter(pk__in=bons)
    allpaid = all(livraison.ispaid for livraison in livraisons)
    
    print('target', target, 'livraisons', livraisons, len(livraisons), len(livraisons)==1, 'date', date)
    isfarah=False
    
    if target=='f':
        isfarah=True
        latest_receipt = Factureachat.objects.filter(
            facture_no__startswith=f'FR-AFC{year}'
        ).last()
        # latest_receipt = Bonsortie.objects.filter(
        #     facture_no__startswith=f'FR-BL{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.facture_no[-9:])
            receipt_no = f"FR-AFC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"FR-AFC{year}000000001"
    else:
        latest_receipt = Factureachat.objects.filter(
            facture_no__startswith=f'AFC{year}'
        ).last()
        # latest_receipt = Bonsortie.objects.filter(
        #     facture_no__startswith=f'FR-BL{year}'
        # ).order_by("-bon_no").first()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.facture_no[-9:])
            receipt_no = f"AFC{year}{latest_receipt_no + 1:09}"
        else:
            receipt_no = f"AFC{year}000000001"
    fc_no=request.GET.get('factureno').upper()
    # check iffacture with numlber already exist
    if not fc_no=='':
        receipt_no=fc_no
    facture=Factureachat.objects.filter(facture_no=fc_no).first()
    print('>> facture ans items if exist',fc_no, facture, facture.bons)
    # there is a facture with the same number and has no bons
    if facture and facture.bons.exists():
        return JsonResponse({
            'success':False,
            'error':'Numero deja exist'
        })
    if facture:
        facture=facture
    else:
        facture=Factureachat.objects.create(
        facture_no=receipt_no,
        supplier_id=supplierid,
        isfarah=isfarah,
        date=date
    )
    total=0
    if allpaid:
        print('>> all bons are paid')
        facture.ispaid=True
        facture.rest=0
    else:
        unpaid_bons = livraisons.filter(ispaid=False)

        # Get the total amount for unpaid bons
        total_unpaid = unpaid_bons.aggregate(total=Sum('total'))['total']
        print('>> not all bons are paid²', total_unpaid)
        facture.rest=total_unpaid
    facture.save()
    for bon in livraisons:
        total+=bon.total
        bon.isfacture=True
        bon.facture=facture
        bon.save()
        # loop items of bon
        items=Stockin.objects.filter(nbon=bon)
        print('items in multiple', items)
        # depricated
        # for i in items:
        #     Outfactureachat.objects.create(
        #         facture=facture,
        #         remise1=i.remise1,
        #         remise2=i.remise2,
        #         remise3=i.remise3,
        #         remise4=i.remise4,
        #         name=i.name,
        #         ref=i.ref,
        #         product=i.product,
        #         qty=i.quantity,
        #         price=i.price,
        #         total=i.total,
        #         supplier_id=supplierid,
        #         date=date,
        #         isfarah=isfarah,
        #         stockin=i
        #     )    
    
    facture.total=total
    facture.bons.set(livraisons)
    facture.save()
    supplier.save()
    return JsonResponse({
        'success':True
    })


def updatebonavoirsupp(request):
    id=request.POST.get('bonid')
    orderno=request.POST.get('orderno')
    note=request.POST.get('note')
    print('>>> order, note', orderno, note)
    target=request.POST.get('target')
    isfarah=target=='f'
    avoir=Avoirsupplier.objects.get(pk=id)
    supplier=Supplier.objects.get(pk=request.POST.get('supplierid'))
    # we need avoir n° cause delete avoir will delete id, id is used in avoir n°
    avoirno=avoir.no
    avoiritems=Returnedsupplier.objects.filter(avoir=avoir)
    totalbon=request.POST.get('totalbon')
    newmode=request.POST.get('mode')
    isfacture=True if newmode=='facture' else False
    print("isfacture", isfacture)
    thissupp=avoir.supplier
    
    for i in avoiritems:
        product=Produit.objects.get(pk=i.product_id)
        if isfarah:
            product.stocktotalfarah=int(product.stocktotalfarah)+int(i.qty)
        else:
            product.stocktotalorgh=int(product.stocktotalorgh)+int(i.qty)
        product.save()
        i.delete()
    avoir.supplier=supplier
    #avoir.representant_id=request.POST.get('repid')
    avoir.total=totalbon
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    avoir.date=datebon
    #avoir.no=request.POST.get('orderno')
    avoir.no=orderno
    avoir.note=note
    avoir.save()
    # update this items


    print('client:', avoir.supplier.id)
    with transaction.atomic():
        for i in json.loads(request.POST.get('products')):
            product=Produit.objects.get(pk=i['productid'])
            if isfarah:
                product.stocktotalfarah=int(product.stocktotalfarah)-int(i['qty'])
            else:
                product.stocktotalorgh=int(product.stocktotalorgh)-int(i['qty'])
            
            product.save()
            Returnedsupplier.objects.create(
                avoir=avoir,
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                isfarah=isfarah
            )
            

    return JsonResponse({
        'success':True
    })

def achatfacture(request):
    target=request.GET.get('target')
    print('target', target)
    if target=='f':
        facture=Factureachat.objects.filter(isfarah=True, isvalid=False).order_by('-id')
    else:
        facture=Factureachat.objects.filter(isorgh=True, isvalid=False).order_by('-id')
    target=request.GET.get('target')
    ctx={
        'title':'List facture achat',
        'factures':facture,
        'target':target,
        'today':timezone.now()
    }
    return render(request, 'listfactureachat.html', ctx)

def cancelbon(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    print('>>> bon', id)
    bon=Bonlivraison.objects.get(pk=id)
    items=Livraisonitem.objects.filter(bon=bon)
    for i in items:
        product=i.product
        if target=='f':
            product.stocktotalfarah+=i.qty
        else:
            product.stocktotalorgh+=i.qty
        product.save()
    bon.iscanceled=True
    bon.save()
    return JsonResponse({
        'success':True
    })

def rastorebon(request):
    id=request.GET.get('id')
    bon=Bonlivraison.objects.get(pk=id)
    items=Livraisonitem.objects.filter(bon=bon)
    for i in items:
        product=i.product
        if bon.isfarah:
            product.stocktotalfarah-=i.qty
        else:
            product.stocktotalorgh-=i.qty
        product.save()
    bon.iscanceled=False
    bon.save()
    return JsonResponse({
        'success':True
    })

def getbonstovalidate(request):
    datefrom=request.GET.get('datefrom')
    dateend=request.GET.get('dateend')
    target=request.GET.get('target')
    mode=request.GET.get('mode')
    isfarah=target=='f'
    print('isfarah', isfarah, 'target', target)
    trs=''
    print('mode>>', mode)
    if mode=='facture':
        bons=Facture.objects.filter(isvalid=False, ispaid=True, date__range=[datefrom, dateend], isfarah=isfarah).order_by('date')
        for i in bons:
            trs+=f'<tr class="blreglrow"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.facture_no}</td><td>{i.total}</td> <td><input type="checkbox" value="{i.id}" name="bonstopay" total={i.total} onchange="checkreglementbox(event)"></td></tr>'
        return JsonResponse({
            'bons':trs,
            'totalbons':round(bons.aggregate(Sum('total')).get('total__sum') or 0, 2),
        })
    bons=Bonlivraison.objects.filter(iscanceled=False, isvalid=False, ispaid=True, date__range=[datefrom, dateend], isfarah=isfarah, isfacture=True).order_by('date')
    for i in bons:
        facture_info = f'facture={i.facture.facture_no}' if i.facture else ""
        print('>>', facture_info)
        trs += f'<tr class="blreglrow"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.total}</td><td><input type="checkbox" value="{i.id}" name="bonstopay" total="{i.total}" {facture_info} onchange="checkreglementbox(event), checksamefacture(event)"></td></tr>'
    return JsonResponse({
        'bons':trs,
        'totalbons':round(bons.aggregate(Sum('total')).get('total__sum') or 0, 2),
    })

def getbonachattovalidate(request):
    datefrom=request.GET.get('datefrom')
    dateend=request.GET.get('dateend')
    target=request.GET.get('target')
    mode=request.GET.get('mode')
    isfarah=target=='f'
    print('isfarah', isfarah, 'target', target)
    trs=''
    if mode=='facture':
        bons=Factureachat.objects.filter(isvalid=False, ispaid=True, date__range=[datefrom, dateend], isfarah=isfarah).order_by('date')
        for i in bons:
            trs+=f'<tr class="blreglrow"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.facture_no}</td><td>{i.total}</td> <td><input type="checkbox" value="{i.id}" name="bonstopay" total={i.total} onchange="checkreglementbox(event)"></td></tr>'
        return JsonResponse({
            'bons':trs,
            'totalbons':round(bons.aggregate(Sum('total')).get('total__sum') or 0, 2),
        })
    bons=Itemsbysupplier.objects.filter(isvalid=False, ispaid=True, date__range=[datefrom, dateend], isfarah=isfarah, isfacture=True).order_by('date')
    for i in bons:
        facture_info = f'facture={i.facture.facture_no}' if i.facture else ""
        print('>>', facture_info)
        trs += f'<tr class="blreglrow"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.nbon}</td><td>{i.total}</td><td><input type="checkbox" value="{i.id}" name="bonstopay" total="{i.total}" {facture_info} onchange="checkreglementbox(event), checksamefacture(event)"></td></tr>'
    return JsonResponse({
        'bons':trs,
        'totalbons':round(bons.aggregate(Sum('total')).get('total__sum') or 0, 2),
    })


def validatebons(request):
    mode=request.GET.get('mode')
    bons=json.loads(request.GET.get('bons'))
    if mode=='facture':
        livraisons=Facture.objects.filter(pk__in=bons)
        for livraison in livraisons:
            print("make bon valid", livraison.bons.all())
            # Update 'ispaid' for related ManyToManyField (bons)
            livraison.bons.all().update(isvalid=True)
    else:
        livraisons=Bonlivraison.objects.filter(pk__in=bons)
        for livraison in livraisons:
            print("make facture valid", livraison.facture)
            # Update 'ispaid' for related ManyToManyField (bons)
            #if livraison.facture.ispaid:
            livraison.facture.isvalid=True
            livraison.facture.ispaid=True
            livraison.facture.save()
    livraisons.update(isvalid=True)
    return JsonResponse({
        'success':True
    })

def validatebonachat(request):
    mode=request.GET.get('mode')
    bons=json.loads(request.GET.get('bons'))
    if mode=='facture':
        livraisons=Factureachat.objects.filter(pk__in=bons)
        for livraison in livraisons:
            print("make bon valid", livraison.bons.all())
            # Update 'ispaid' for related ManyToManyField (bons)
            livraison.bons.all().update(isvalid=True)
    else:
        livraisons=Itemsbysupplier.objects.filter(pk__in=bons)
        for livraison in livraisons:
            print("make facture valid", livraison.facture.facture_no)
            # Update 'ispaid' for related ManyToManyField (bons)
            livraison.facture.ispaid=True
            livraison.facture.isvalid=True
            livraison.facture.save()
    livraisons.update(isvalid=True)
    return JsonResponse({
        'success':True
    })


def cancelfacture(request):
    id=request.GET.get('id')
    facture=Facture.objects.get(pk=id)
    facture.iscanceled=True
    return JsonResponse({
        'success':True
    })

def cancelavoir(request):
    id=request.GET.get('id')
    avoir=Avoirclient.objects.get(pk=id)
    avoir.iscanceled=True
    return JsonResponse({
        'success':True
    })

def getbonvalider(request):
    target=request.GET.get('target')
    isfarah=target=='f'
    bons = Bonlivraison.objects.filter(isfarah=isfarah, isvalid=True).order_by('-bon_no')[:50]
    
    ctx={
        'html':render(request, 'bllist.html', {'bons':bons, 'target':target, "mode": 'valid'}).content.decode('utf-8'),
        'total':0,
    }
    if bons:
        ctx['total']=round(bons.aggregate(Sum('total')).get('total__sum'), 2)
    return JsonResponse(ctx)
def getbonachatvalider(request):
    target=request.GET.get('target')
    isfarah=target=='f'
    bons = Itemsbysupplier.objects.filter(isfarah=isfarah, isvalid=True).order_by('-nbon')[:50]
    print('>> bons', bons)
    ctx={
        'html':render(request, 'bonachatlist.html', {'bons':bons, 'target':target, "mode": 'valid'}).content.decode('utf-8'),
        'total':0,
    }
    if bons:
        ctx['total']=round(bons.aggregate(Sum('total')).get('total__sum'), 2)
    return JsonResponse(ctx)

def getfacturevalider(request):
    target=request.GET.get('target')
    isfarah=target=='f'
    factures = Facture.objects.filter(isfarah=isfarah, isvalid=True).order_by('-facture_no')[:50]
    ctx={
        'html':render(request, 'fclist.html', {'bons':factures, 'target':target}).content.decode('utf-8'),
        'total':0,
    }
    if factures:
        ctx['total']=round(factures.aggregate(Sum('total')).get('total__sum'), 2)
    return JsonResponse(ctx)

def getfactureachatvalider(request):
    target=request.GET.get('target')
    isfarah=target=='f'
    factures = Factureachat.objects.filter(isfarah=isfarah, isvalid=True).order_by('-facture_no')[:50]
    ctx={
        'html':render(request, 'fcachatlist.html', {'bons':factures, 'target':target}).content.decode('utf-8'),
        'total':0,
    }
    if factures:
        ctx['total']=round(factures.aggregate(Sum('total')).get('total__sum'), 2)
    return JsonResponse(ctx)


def getcanceledbons(request):
    target=request.GET.get('target')
    isfarah=target=='f'
    bons = Bonlivraison.objects.filter(isfarah=isfarah, iscanceled=True).order_by('-bon_no')[:50]
    print('>> bons', bons)
    return JsonResponse({
        'html':render(request, 'bllist.html', {'bons':bons, 'target':target}).content.decode('utf-8'),
        'total':round(bons.aggregate(Sum('total')).get('total__sum'), 2),
    })

def validation(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Validation',
        #'boncommand':Order.objects.filter(isdelivered=False).exclude(note__icontains='Reliquat').count(),
        #'depasser':depasser,
        #'reps':Represent.objects.all(),
        'target':target
    }
    return render(request, 'validation.html', ctx)

def printbarcode(request):
    products=json.loads(request.GET.get('products'))
    supplierid=request.GET.get('supplierid')
    date=request.GET.get('date')
    date=datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%y')
    target=request.GET.get('target')
    isfarah=target=='f'
    barcodes = []
    for i in products:
        if isfarah:
            ref='fr-'+i['ref']
        else:
            ref=i['ref']
        print('>>> ref', ref)
        name=i['name']
        remise1=0 if i['remise1']=='' else int(i['remise1'])
        price=i['price']
        net=float(price)-(float(price)*int(remise1)/100)
        price=round(net*2, 2)
        #price=str(price).replace('.', '')
        qty=i['qty']
        print('>>>', supplierid, date)
        # # List to hold the barcodes in base64 format
        
        # Generate barcodes for the specified quantity
        thisbarcodes=[]
        # for _ in range(int(qty)):
        #     buffer = BytesIO()
        #     barcode_instance = code_class(ref, writer=ImageWriter())
        #     options = {
        #         'write_text': False,
        #         'dpi': 300,           # Adjust module width for precision
        #         #'module_width': barcode_width_inches,
        #         'module_height': 0.8,
        #     }
        #     barcode_instance.write(buffer, options)

        #     # Convert the image to base64 and append it to the list
        #     barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        #     thisbarcodes.append([ref, name, price, barcode_base64])
        #     buffer.close()
        # barcodes.append(thisbarcodes)
        for _ in range(int(qty)):
            buffer = BytesIO()
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR code
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=0,
            )
            qr.add_data(ref)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            img.save(buffer, format="PNG")
            # get 2 digits of price %2
            
            # Convert the image to base64 and append it to the list
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            thisbarcodes.append([ref, name, f"{price:.2f}".replace('.', ''), qr_base64, supplierid, date])
            buffer.close()
        barcodes.append(thisbarcodes)
        
        # if achat means the request is coming from bon achat, date will be today
    return render(request, 'barcode.html', {
        'barcodes': barcodes,
    })

def barcodepdct(request):
    ref=request.GET.get('ref').lower()
    target=request.GET.get('target')
    product=Produit.objects.get(ref=ref)
    return JsonResponse({
        'data':f"{product.ref}§{product.name}§{product.buyprice}§{product.stocktotalfarah if target=='f' else product.stocktotalorgh}§{product.stockfacturefarah if target=='f' else product.stocktotalorgh}§{product.id}§{product.frsellprice if target=='f' else product.sellprice}§{product.frremisesell if target=='f' else product.remisesell}§{product.prixnet}§{product.representprice}",
    })

def getlastbuyprice(request):
    id=request.GET.get('id')
    target=request.GET.get('target')
    isfarah=target=='f'
    print('>>> isfarah', isfarah)
    product=Produit.objects.filter(pk=id).last()
    dp=0
    remise=0
    if product:
        if isfarah:
            dp=product.frbuyprice
            remise=product.frremise1
        
    return JsonResponse({
        'remise':remise,
        'dp':dp
    })

def modifierbonsortie(request):
    id=request.GET.get('id')
    bon=Bonsortie.objects.get(pk=id)
    items=Sortieitem.objects.filter(bon=bon)
    ctx={
        'title':'Modifier '+bon.bon_no,
        'items':items,
        'bon':bon,
        'cars':Carlogos.objects.all(),
        # 'products':Produit.objects.all(),
        # 'clients':Client.objects.all(),
    }
    return render(request, 'modifierbonsortie.html', ctx)

def updatebonsortie(request):
    clientid=request.POST.get('clientid')
    car=request.POST.get('car')
    remise=request.POST.get('remise')=='true'
    print('>>>', remise)
    #repid=request.POST.get('repid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    bonid=request.POST.get('bonid')
    # orderno
    #transport=request.POST.get('transport')
    note=request.POST.get('note')
    payment=request.POST.get('payment')
    print('>>>>>>', products, totalbon, payment)
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    client=Client.objects.get(pk=clientid)
    bon=Bonsortie.objects.get(pk=bonid)
    bon.date=datebon
    bon.client=client
    bon.total=totalbon
    bon.car=car
    bon.note=note
    bon.remise=remise
    items=Sortieitem.objects.filter(bon=bon)
    #initiate stock and price history
    for i in items:
        product=i.product
        # stock
        if i.isfarah:
            product.stocktotalfarah+=i.qty
        else:
            product.stockfactureorgh+=i.qty
        product.save()
        #print('>> qtyofprice, qties', json.loads(i.pricesofout), json.loads(i.qtyofout))
        # prices and qties of prices
        # for pr, qty in zip(json.loads(i.pricesofout), json.loads(i.qtyofout)):
        #     st=Stockin.objects.get(pk=pr)
        #     st.qtyofprice+=qty
        #     st.save()
        i.delete()

    with transaction.atomic():
        for i in json.loads(products):
            farah=i['farah']=='1'
            product=Produit.objects.get(pk=i['productid'])
            #create sortie items
            sortitem=Sortieitem.objects.create(
                bon=bon,
                remise=i['remise'],
                name=i['name'],
                ref=i['ref'],
                product=product,
                qty=i['qty'],
                price=i['price'],
                total=i['total'],
                client_id=clientid,
                date=datebon,
                isfarah=farah,
            )
        
            # update stock accordinly
            if farah:
                product.stocktotalfarah=float(product.stocktotalfarah)-float(i['qty'])
                # negative=json.loads(product.frnegative)
                # sorties=json.loads(product.frsorties)
                # if float(product.stocktotalfarah)-float(i['qty'])<0:
                #     product.isnegativeinfr=True
                #     negative.append(float(i['qty'])-float(product.stocktotalfarah))
                #     sorties.append(sortitem.id)
                # product.frnegative=negative
                # product.frsorties=sorties
            else:
                product.stocktotalorgh=float(product.stocktotalorgh)-float(i['qty'])
                # negative=json.loads(product.negative)
                # sorties=json.loads(product.sorties)
                # negative=json.loads(product.negative)
                # sorties=json.loads(product.sorties)
                # if float(product.stocktotalorgh)-float(i['qty'])<0:
                #     product.isnegative=True
                #     negative.append(float(i['qty'])-float(product.stocktotalfarah))
                #     sorties.append(sortitem.id)
                # product.negative=negative
                # product.sorties=sorties
            product.save()
            
            # update prices accordinly
            # pri lli7diffo' d mnchk addifo4n 4kola pri
            # pricesofout=[]
            # qtyofout=[]
            # prices=Stockin.objects.filter(qtyofprice__gt=0, isfarah=farah, product=product, isavoir=False).order_by('id')
            # thisqty=int(i['qty'])
            # print('>>> qty', thisqty)
            # for pr in prices:
            #     print('>> qty', thisqty, pr.product.ref, pr.qtyofprice, pr.price)
            #     if not thisqty<=0:
            #         print('>> qty is not 0')
            #         if pr.qtyofprice<=thisqty:
            #             thisqty=thisqty-int(pr.qtyofprice)
            #             qtyofout.append(pr.qtyofprice)
            #             pr.qtyofprice=0
            #             pricesofout.append(pr.id)
            #         else:
            #             pr.qtyofprice=int(pr.qtyofprice)-thisqty
            #             qtyofout.append(thisqty)
            #             thisqty=0
            #             pricesofout.append(pr.id)
            #         pr.save()
            #     else:
            #         print('>> qty', thisqty, pr.product.ref, 'breaking')
            #         break
            # sortitem.pricesofout=pricesofout
            # sortitem.qtyofout=qtyofout
            # sortitem.save()
    # if float(payment)>0:
    #     PaymentClientbl.objects.create(
    #         client_id=clientid,
    #         amount=payment,
    #         date=date.today(),
    #         mode='espece',
    #         npiece=f'Paiement de bon de sortie {bon.bon_no}',
    #         issortie=True
    #     )
    # if float(payment)<float(totalbon):
    #     if remise:
    #         bon.ispaid=True
    #         bon.remiseamount=round(float(totalbon)-float(payment), 2)
    #     else:
    #         bon.rest=round(float(totalbon)-float(payment), 2)
    #         Avanceclient.objects.create(
    #             client_id=clientid,
    #             amount=payment,
    #             #today
    #             date=timezone.now().date(),
    #             npiece=f'Avance de bon de sortie {bon.bon_no}',
    #             issortie=True
    #         )
    # if float(payment)==float(totalbon):
    #     bon.ispaid=True
    #     PaymentClientbl.objects.create(
    #         client_id=clientid,
    #         amount=payment,
    #         date=date.today(),
    #         mode='espece',
    #         npiece=f'Paiement de bon de sortie {bon.bon_no}',
    #         issortie=True
    #     )
    # payment = PaymentClientbl.objects.annotate(
    #     bonsortie_count=Count('bonsortie')
    # ).filter(
    #     bonsortie_count=1,  # Ensure it has exactly one Bonsortie
    #     bonsortie__id=4    # Ensure the Bonsortie has ID 4
    # ).first()
    # bonsortie=payment.bonsortie.all()
    # bonsortie.update(ispaid=False)
    # bonsortie.update(remise=False)
    # bonsortie.update(paidamount=0.0)
    # bonsortie.update(remiseamount=0.0)
    if float(payment)>0:
        if remise:
            print('>> Remise')
            bon.remise=True
            bon.remiseamount=round(float(totalbon)-float(payment), 2)
        bon.ispaid=True
        regl=PaymentClientbl.objects.create(
            client_id=clientid,
            amount=payment,
            date=date.today(),
            mode='espece',
            #npiece=f'Paiement de bon de sortie {bon.bon_no}',
            npiece=f'espece',
            issortie=True
        )
        regl.bonsortie.set([bon])
    
    
    bon.save()
    return JsonResponse({
        'success':True
    })

def removebonfromfacture(request):
    factureid=request.GET.get('factureid')
    bonid=request.GET.get('bonid')
    facture=Facture.objects.get(pk=factureid)
    bon=Bonlivraison.objects.get(pk=bonid)
    bon.isfacture=False
    bon.save()
    facture.bons.remove(bon)
    facture.total-=bon.total
    facture.save()
    return JsonResponse({
        'success':True
    })

def removebonfromfactureachat(request):
    factureid=request.GET.get('factureid')
    bonid=request.GET.get('bonid')
    facture=Factureachat.objects.get(pk=factureid)
    bon=Itemsbysupplier.objects.get(pk=bonid)
    bon.isfacture=False
    bon.save()
    facture.bons.remove(bon)
    facture.total-=bon.total
    facture.save()
    return JsonResponse({
        'success':True
    })

def removebonfromregl(request):
    reglid=request.GET.get('reglid')
    bonid=request.GET.get('bonid')
    bon=Bonlivraison.objects.get(pk=bonid)
    regl=PaymentClientbl.objects.get(pk=reglid)
    print('>>> bon', bon)
    bon.ispaid=False
    bon.save()
    regl.bons.remove(bon)
    regl.save()
    return JsonResponse({
        'success':True
    })

def removeavoirfromregl(request):
    reglid=request.GET.get('reglid')
    avoirid=request.GET.get('avoirid')
    avoir=Avoirclient.objects.get(pk=avoirid)
    regl=PaymentClientbl.objects.get(pk=reglid)
    regl.avoirs.remove(avoir)
    regl.save()
    avoir.inreglement=False
    avoir.save()
    return JsonResponse({
        'success':True
    })

def removeavancefromregl(request):
    reglid=request.GET.get('reglid')
    avanceid=request.GET.get('avanceid')
    avance=Avanceclient.objects.get(pk=avanceid)
    regl=PaymentClientbl.objects.get(pk=reglid)
    regl.avances.remove(avance)
    regl.save()
    avance.inreglement=False
    avance.save()
    print('>> avance', avance)
    return JsonResponse({
        'success':True
    })

def deletereglementclient(request):
    reglid=request.GET.get('reglid')
    reglement=PaymentClientbl.objects.get(pk=reglid)
    avoirs=reglement.avoirs.all()
    bons=reglement.bons.all()
    bonsortie=reglement.bonsortie.all()
    avances=reglement.avances.all()
    factures=reglement.factures.all()
    if factures:
        for i in factures:
            bons=i.bons.all()
            # for i in bons:
            #     i.ispaid=False
            #     i.isvalid=False
            #     i.save()
            bons.update(ispaid=False)
            bons.update(isvalid=False)
    avoirs.update(inreglement=False)
    bonsortie.update(ispaid=False)
    bonsortie.update(remise=False)
    bonsortie.update(paidamount=0.0)
    bonsortie.update(remiseamount=0.0)
    avances.update(inreglement=False)
    bons.update(ispaid=False)
    bons.update(isvalid=False)
    factures.update(ispaid=False)
    factures.update(rest=0)
    reglement.delete()
    return JsonResponse({
        'success':True
    })


def deletereglementsupplier(request):
    reglid=request.GET.get('reglid')
    reglement=PaymentSupplier.objects.get(pk=reglid)
    avoirs=reglement.avoirs.all()
    bons=reglement.bons.all()
    avances=reglement.avances.all()
    factures=reglement.factures.all()
    if factures:
        for i in factures:
            bons=i.bons.all()
            # for i in bons:
            #     i.ispaid=False
            #     i.isvalid=False
            #     i.save()
            bons.update(ispaid=False)
            bons.update(isvalid=False)
    avoirs.update(inreglement=False)
    avances.update(inreglement=False)
    bons.update(ispaid=False)
    bons.update(isvalid=False)
    factures.update(ispaid=False)
    factures.update(rest=0)
    reglement.delete()
    return JsonResponse({
        'success':True
    })

def updatebonsoffacture(request):
    factureid=request.GET.get('factureid')
    facture=Facture.objects.get(pk=factureid)
    
    bons=json.loads(request.GET.get('bons'))
    print('>> facture, bons', facture, bons)
    livraisons=Bonlivraison.objects.filter(pk__in=bons)
    livraisons.update(isfacture=True)
    # livraison_ids = livraisons.values_list('id', flat=True)
    facture.bons.add(*livraisons)
    return JsonResponse({
        'success':True
    })