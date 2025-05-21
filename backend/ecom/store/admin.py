from django.contrib import admin
from.models import Category, Customer, Product, Order, Profile
from django.contrib.auth.models import User



admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Profile)


#mix profile info and user info

class ProfileInLine(admin.StackedInline):
    model = Profile

#extend the user profile
class UserAdmin(admin.ModelAdmin):
    model = User
    field = ["username", "first_name", "last_name", "email"]
    inlines = [ProfileInLine]


#unregister the default user admin
admin.site.unregister(User)
#register the new user admin
admin.site.register(User, UserAdmin)