
from django.urls import path
from . import views
from django.views.defaults import page_not_found
urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:id>', views.product, name='product'),
    path('clientdashboar', views.clientdashboar, name='clientdashboar'),
    path('searchref', views.searchref, name='searchref'),
    path('filters', views.filters, name='filters'),
    path('create', views.create, name='create'),
    path('addcategory', views.addcategory, name='addcategory'),
    path('addbrand', views.addbrand, name='addbrand'),
    path('addmark', views.addmark, name='addmark'),
    path('addbulk', views.addbulk, name='addbulk'),
    path('commande', views.commande, name='commande'),
    path('orders', views.orders, name='orders'),
    path('orderitems/<int:id>', views.orderitems),
    path('dilevered/<int:id>', views.dilevered),
    path('paied/<int:id>', views.paied),
    path('marks/products/<int:id>', views.products),
    path('categories/products/<int:id>', views.productscategories, name='productscategories'),
    path('marques/products/<int:id>', views.productsmarks),
    path('login', views.loginpage, name='loginpage'),
    path('system', views.system, name='system'),
    path('catalog', views.catalog, name='catalog'),
    path('salsemanorders/<str:str_id>', views.salsemanorders, name='salsemanorders'),
    path('logoutuser', views.logoutuser, name='logoutuser'),
    path('clients', views.clients, name='clients'),
    path('addclient', views.addclient, name='addclient'),
    path('aboutus', views.aboutus, name='aboutus'),
    path('partners', views.partners, name='marques'),
    path('profile', views.profile, name='profile'),
    path('editinfoclient', views.editinfoclient, name='editinfoclient'),
    path('updatepassword', views.updatepassword, name='updatepassword'),
    path('developer', views.developer, name='developer'),
    path('create_product', views.create_product, name='create_product'),
    path('cart', views.cart, name='cart'),
    path('ordersforeach', views.ordersforeach, name='ordersforeach'),
    path('sitemap', views.sitemap, name='sitemap'),
    path('makeuserconnected', views.makeuserconnected, name='makeuserconnected'),
    path('loginuser', views.loginuser, name='login'),
    path('catalogpage', views.catalogpage, name='catalogpage'),
    path('client/clientshome', views.clientshome, name='clientshome'),
    path('client/searchglobal', views.searchglobal, name='searchglobal'),
    path('productdata', views.productdata, name='productdata'),
    path('searchrefphone', views.searchrefphone, name='searchrefphone'),
    path('addtocart', views.addtocart, name='addtocart'),
    path('removeitemfromcart', views.removeitemfromcart, name='removeitemfromcart'),
    path('removecart', views.removecart, name='removecart'),
    path('getitemsincart', views.getitemsincart, name='getitemsincart'),
    path('b3921b', views.b3921b, name='b3921b'),
    path('client/api/getproduct', views.apiproduct, name='apiproduct'),
    path('.well-known/pki-validation/F62561CD3B31648820E023E571F1992F.txt', views.validation, name='validation'),
    path('commandfromserver', views.commandfromserver, name='commandfromserver'),
    path('updatecartitem', views.updatecartitem, name='updatecartitem'),
    path('addtowhishlist', views.addtowhishlist, name='addtowhishlist'),
    path('getitemsinwishlist', views.getitemsinwishlist, name='getitemsinwishlist'),
    path('replicata', views.replicata, name='replicata'),
    path('removeitemfromcart', views.removeitemfromcart, name='removeitemfromcart'),
    path('removeitemfromwish', views.removeitemfromwish, name='removeitemfromwish'),
    path('switchtocart', views.switchtocart, name='switchtocart'),
    path('updatewishitem', views.updatewishitem, name='updatewishitem'),
    path('catalogpermission', views.catalogpermission, name='catalogpermission'),
    path('notifications', views.notifications, name='notifications'),
    path('newarrivage', views.newarrivage, name='newarrivage'),
    path('allproducts', views.allproducts, name='allproducts'),
    path('contactform', views.contactform, name='contactform'),
    path('addtocartrep', views.addtocartrep, name='addtocartrep'),
    path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    path('updaterepcartitem', views.updaterepcartitem, name='updaterepcartitem'),
    path('removeitemfromrepcart', views.removeitemfromrepcart, name='removeitemfromrepcart'),
    path('repcommande', views.repcommande, name='repcommande'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),
    # path('getitemsinrepcart', views.getitemsinrepcart, name='getitemsinrepcart'),

]
