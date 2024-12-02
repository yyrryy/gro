from django.shortcuts import render, redirect
from main.models import Produit, Mark, Category, Supplier, Stockin, Itemsbysupplier, Client, Represent, Order, Orderitem, Clientprices, Bonsortie, Facture, Outfacture, Livraisonitem, PaymentClientbl, PaymentClientfc,  PaymentSupplier, Bonsregle, Returnedsupplier, Avoirclient, Returned, Avoirsupplier, Orderitem, Carlogos, Ordersnotif, CommandItem, DeviItem, Sortieitem, Devi, Bonlivraison, Command, CommandItemsupplier, DeviItemsupplier, Devisupplier, Commandsupplier
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, F, Sum, Q, ExpressionWrapper, Func, fields, IntegerField
from datetime import datetime, date, timedelta
from django.utils import timezone
import json
from django.db import transaction

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
    return render(request, 'fdashboard.html')

# ste1=Farah
def ste2(request):
    return render(request, 'odashboard.html')

def pointdevente(request):
    return render(request, 'pos.html')

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
    print('>>>>>>', receipt_no)
    return render(request, 'bonsortie.html', {
        'title':'Bon de Sortie',
        # 'clients':Client.objects.all(),
        # # 'products':Produit.objects.all(),
        # 'commercials':Represent.objects.all(),
    })

def addbonsortie(request):

    #current_time = datetime.now().strftime('%H:%M:%S')
    clientid=request.POST.get('clientid')
    #repid=request.POST.get('repid')
    products=request.POST.get('products')
    totalbon=request.POST.get('totalbon')
    orderid=request.POST.get('orderid', None)
    # orderno
    #transport=request.POST.get('transport')
    note=request.POST.get('note')
    payment=request.POST.get('payment')
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
        client_id=clientid,
        total=totalbon,
        date=datebon,
        bon_no=receipt_no,
        note=note,
        user=request.user,
        paidamount=payment
    )
    print('>>>>>>', len(json.loads(products))>0)
    if len(json.loads(products))>0:
        with transaction.atomic():
            
            for i in json.loads(products):
                farah=i['farah']=='1'
                product=Produit.objects.get(pk=i['productid'])
                Sortieitem.objects.create(
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
                    isfarah=farah
                )
            
            
                if farah:
                    product.stocktotalfarah=float(product.stocktotalfarah)-float(i['qty'])
                else:
                    product.stocktotalorgh=float(product.stocktotalorgh)-float(i['qty'])
                product.save()

    if float(payment)>0:
        PaymentClientbl.objects.create(
            client_id=clientid,
            amount=payment,
            date=date.today(),
            mode='espece',
            npiece=f'Paiement de bon de sortie {order.bon_no}'
        )
        if float(payment)<float(totalbon):
            order.rest=round(float(totalbon)-float(payment), 2)
        if float(payment)==float(totalbon):
            order.ispaid=True
        order.save()
    

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
            livraison_data['ref']=i.ref.replace('(FR) ', ''),
            livraison_data['isfarah'] = True
            farahitems.append(Livraisonitem(**livraison_data))
        else:
            totalorgh += item_total
            livraison_data['ref']=i.ref.replace('(OR) ', ''),
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
            'date': timezone.now(),
            'bon_no': receipt_no,
            'note': bon.note,
            'bonsortie':bon
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
    return render(request, 'orghhome.html', {'target':'f'})

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
    ctx={
        'title':f'Bon de livraison {order.bon_no}',
        'order':order,
        'orderitems':orderitems,
        'bonsortie':True
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
    price=0
    remise=0
    buyprice=product.frbuyprice if 'fr' in term else product.buyprice
    remisebuyprice=product.frremise1 if 'fr' in term else product.remise1
    try:
            clientprice=Sortieitem.objects.filter(client_id=clientid, product_id=pdctid).last()
            price=clientprice.price
            remise=clientprice.remise
            return JsonResponse({
                'price':price,
                'remise':remise,
                'buyprice':buyprice,
                'remisebuyprice':remisebuyprice
            })
    except:
        return JsonResponse({
            'price':0,
            'remise':0,
            'buyprice':buyprice,
            'remisebuyprice':remisebuyprice
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

    return render(request, 'devitoboncommand.html', ctx)
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
            bon_no__startswith=f'FR-BC{year}'
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
    if devid is not None:
        devi=Devisupplier.objects.get(pk=devid)
        devi.generatedbc=True
        devi.bc=order
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
def supplierboncommandobl(request):
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
        bons=Bonsortie.objects.filter(client_id=clientid, isfacture=False).order_by('date')[:50]
        total=round(Bonsortie.objects.filter(client_id=clientid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    else:
        bons=Bonlivraison.objects.filter(client_id=clientid, isfacture=False).order_by('date')[:50]
        total=round(Bonlivraison.objects.filter(client_id=clientid).aggregate(Sum('total')).get('total__sum')or 0,  2)
    trs=''
    for i in bons:
        # old code, if reglement is paid it's checked from here
        # trs+=f'<tr style="background: {"rgb(221, 250, 237);" if i.reglements.exists() else ""}" class="blreglrow" clientid="{clientid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.client.name}</td><td>{i.total}</td><td class="text-danger">{"RR" if i.reglements.exists() else "NR"}</td> <td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)" {"checked" if i.reglements.exists() else ""}></td></tr>'
        trs+=f'<tr class="blreglrow" clientid="{clientid}"><td>{i.date.strftime("%d/%m/%Y")}</td><td>{i.bon_no}</td><td>{i.client.name}</td><td>{i.total}</td><td><input type="checkbox" value="{i.id}" name="bonstopay" onchange="checkreglementbox(event)"></td></tr>'


    return JsonResponse({
        'trs':trs,
        'total':total,
        'soldbl':round(Client.objects.get(pk=clientid).soldbl, 2)
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
    total=0
    facture=Facture.objects.create(
        facture_no=receipt_no,
        client_id=clientid,
        isfarah=isfarah
    )
    # if we have just one bon
    if len(livraisons)==1:
        print(">> here")
        bon=livraisons[0]
        bon.facture=facture
        facture.total=livraisons[0].total
        facture.bon=bon
        bon.isfacture=True
        bon.save()
        #get items of bon
        items=Livraisonitem.objects.filter(bon=bon)
        # create facture items
        for i in items:
            Outfacture.objects.create(
                facture=facture,
                remise=i.remise,
                name=i.name,
                ref=i.ref,
                product=i.product,
                qty=i.qty,
                price=i.price,
                total=i.total,
                client_id=clientid,
                date=date,
                isfarah=isfarah
            )
        # sold facture
        client.soldfacture+=bon.total
    else:
        # iterate throu bons
        for bon in livraisons:
            total+=bon.total
            bon.isfacture=True
            bon.facture=facture
            bon.save()
            # loop items of bon
            items=Livraisonitem.objects.filter(bon=bon)
            for i in items:
                Outfacture.objects.create(
                    facture=facture,
                    remise=i.remise,
                    name=i.name,
                    ref=i.ref,
                    product=i.product,
                    qty=i.qty,
                    price=i.price,
                    total=i.total,
                    client_id=clientid,
                    date=date,
                    isfarah=isfarah
                )    
        facture.total=total
        facture.bons.set(livraisons)
        client.soldfacture+=total
    facture.save()
    client.save()
    return JsonResponse({
        'success':True
    })

def achatfacture(request):
    target=request.GET.get('target')
    return render(request, 'listfactureachat.html')
