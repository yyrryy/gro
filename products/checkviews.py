from django.shortcuts import render, redirect
from main.models import Produit, Mark, Category, Supplier, Stockin, Itemsbysupplier, Client, Represent, Order, Orderitem, Clientprices, Bonsortie, Facture, Outfacture, Livraisonitem, PaymentClientbl, PaymentClientfc,  PaymentSupplier, Bonsregle, Returnedsupplier, Avoirclient, Returned, Avoirsupplier, Orderitem, Carlogos, Ordersnotif, Connectedusers, Promotion, Sortieitem, Bonlivraison
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
    bl=Bonsortie.objects.exclude(pk=id).filter(bon_no=no).first()
    
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
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(f'{datebon}', '%Y-%m-%d')
    client=Client.objects.get(pk=clientid)
    # client.soldtotal=round(float(client.soldtotal)+float(totalbon), 2)
    # client.soldbl=round(float(client.soldbl)+float(totalbon), 2)
    # client.save()
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
        note=note
    )
    print('>>>>>>', len(json.loads(products))>0)
    if len(json.loads(products))>0:
        with transaction.atomic():
            farahitems=[]
            orghitems=[]
            totalfarah=0
            totalorgh=0
            for i in json.loads(products):
                farah=i['farah']=='1'
                product=Produit.objects.get(pk=i['productid'])
                if farah:
                    totalfarah+=float(i['total'])
                    product.stocktotalfarah=int(product.stocktotalfarah)-int(i['qty'])
                    livraisonfarah=Livraisonitem.objects.create(
                        total=i['total'],
                        qty=i['qty'],
                        product=product,
                        price=i['price'],
                        client_id=clientid,
                        date=datebon,
                        isfarah=True
                    )
                    farahitems.append(livraisonfarah)
                else:
                    totalorgh+=float(i['total'])
                    product.stocktotalorgh=int(product.stocktotalorgh)-int(i['qty'])
                    livraisonorgh=Livraisonitem.objects.create(
                        total=i['total'],
                        qty=i['qty'],
                        product=product,
                        price=i['price'],
                        client_id=clientid,
                        date=datebon,
                        isorgh=True
                    )
                    orghitems.append(livraisonorgh)
                #product.stocktotal=int(product.stocktotal)-int(i['qty'])
                product.save()
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
            if len(farahitems)>0:
                latest_receipt = Bonlivraison.objects.filter(
                    bon_no__startswith=f'FR-BL{year}'
                ).last()
                # latest_receipt = Bonsortie.objects.filter(
                #     bon_no__startswith=f'FR-BL{year}'
                # ).order_by("-bon_no").first()
                if latest_receipt:
                    latest_receipt_no = int(latest_receipt.bon_no[-9:])
                    receipt_no = f"FR-BL{year}{latest_receipt_no + 1:09}"
                else:
                    receipt_no = f"FR-BL{year}000000001"
                # create bon livraison in farah
                bon=Bonlivraison.objects.create(
                    client_id=clientid,
                    total=totalfarah,
                    date=datebon,
                    bon_no=receipt_no,
                    note=note,
                    isfarah=True
                )
                # assign bons
                for i in farahitems:
                    i.bon=bon
                    i.save()
            if len(orghitems)>0:
                latest_receipt = Bonlivraison.objects.filter(
                    bon_no__startswith=f'BL{year}'
                ).last()
                # latest_receipt = Bonsortie.objects.filter(
                #     bon_no__startswith=f'BL{year}'
                # ).order_by("-bon_no").first()
                if latest_receipt:
                    latest_receipt_no = int(latest_receipt.bon_no[-9:])
                    receipt_no = f"BL{year}{latest_receipt_no + 1:09}"
                else:
                    receipt_no = f"BL{year}000000001"
                # create bon livraison in orgh
                bon=Bonlivraison.objects.create(
                    client_id=clientid,
                    total=totalorgh,
                    date=datebon,
                    bon_no=receipt_no,
                    note=note,
                    isorgh=True
                )
                # assign bons
                for i in orghitems:
                    i.bon=bon
                    i.save()
                
            


    # increment it
    return JsonResponse({
        "success":True
    })
