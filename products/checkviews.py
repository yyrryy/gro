from django.shortcuts import render, redirect
from main.models import Produit, Mark, Category, Supplier, Stockin, Itemsbysupplier, Client, Represent, Order, Orderitem, Clientprices, Bonsortie, Facture, Outfacture, Livraisonitem, PaymentClientbl, PaymentClientfc,  PaymentSupplier, Bonsregle, Returnedsupplier, Avoirclient, Returned, Avoirsupplier, Orderitem, Carlogos, Ordersnotif, Connectedusers, DeviItem, Sortieitem, Devi, Bonlivraison
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
            'ref': i.ref,
            'name': i.name,
            'product': product,
            'price': i.price,
            'client': i.client,
            'date': timezone.now()
        }

        if i.isfarah:
            totalfarah += item_total
            livraison_data['isfarah'] = True
            farahitems.append(Livraisonitem(**livraison_data))
        else:
            totalorgh += item_total
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
        }
        
        if is_farah:
            bon_data['isfarah'] = True
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
    if target=='f':
        bons=Devi.objects.filter(isfarah=True).order_by('-bon_no')[:50]
    else:
        bons=Devi.objects.filter(isorgh=True).order_by('-bon_no')[:50]
    ctx={
        'title':'Devi',
        'bons':Devi.objects.all().order_by('-bon_no')[:50],
        'target':target
    }
    return render(request, 'listdevi.html', ctx)
def bondevi(request):
    target=request.GET.get('target')
    
    ctx={
        'title':'Bon de Devi',
        'target':target
    }
    return render(request, 'bondevi.html', ctx)

def createdevi(request):
    target=request.GET.get('target')
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
        isorgh=isorgh
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


