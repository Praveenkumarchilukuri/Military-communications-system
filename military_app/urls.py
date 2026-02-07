from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('AdminLogin', views.AdminLogin, name='AdminLogin'),
    path('UserLogin', views.UserLogin, name='UserLogin'),
    path('Signup', views.Signup, name='Signup'),
    path('AdminLoginAction', views.AdminLoginAction, name='AdminLoginAction'),
    path('UserLoginAction', views.UserLoginAction, name='UserLoginAction'),
    path('SignupAction', views.SignupAction, name='SignupAction'),
    
    # Colonel
    path('SendColonelMessages', views.SendColonelMessages, name='SendColonelMessages'),
    path('SendColonelMessagesAction', views.SendColonelMessagesAction, name='SendColonelMessagesAction'),
    path('ViewColonelMessages', views.ViewColonelMessages, name='ViewColonelMessages'),
    path('ReadColonelMessageView', views.ReadColonelMessageView, name='ReadColonelMessageView'),
    path('ReadColonelMessage', views.ReadColonelMessage, name='ReadColonelMessage'),
    
    # Brigadier
    path('SendBrigadierMessages', views.SendBrigadierMessages, name='SendBrigadierMessages'),
    path('SendBrigadierMessagesAction', views.SendBrigadierMessagesAction, name='SendBrigadierMessagesAction'),
    path('ViewBrigadierMessages', views.ViewBrigadierMessages, name='ViewBrigadierMessages'),
    path('ReadBrigadierMessageView', views.ReadBrigadierMessageView, name='ReadBrigadierMessageView'),
    path('ReadBrigadierMessage', views.ReadBrigadierMessage, name='ReadBrigadierMessage'),
    path('ApproveColonel', views.ApproveColonel, name='ApproveColonel'),
    path('ApproveColonelUser', views.ApproveColonelUser, name='ApproveColonelUser'),
    
    # Major
    path('SendMessages', views.SendMessages, name='SendMessages'),
    path('SendMessagesAction', views.SendMessagesAction, name='SendMessagesAction'),
    path('ViewMajorMessages', views.ViewMajorMessages, name='ViewMajorMessages'),
    path('ReadMajorMessageView', views.ReadMajorMessageView, name='ReadMajorMessageView'),
    path('ReadMajorMessage', views.ReadMajorMessage, name='ReadMajorMessage'),
    path('ApproveBrigadier', views.ApproveBrigadier, name='ApproveBrigadier'),
    path('ApproveBrigadierUser', views.ApproveBrigadierUser, name='ApproveBrigadierUser'),
    
    # Admin
    path('ApproveMajor', views.ApproveMajor, name='ApproveMajor'),
    path('ApproveMajorUser', views.ApproveMajorUser, name='ApproveMajorUser'),
]
