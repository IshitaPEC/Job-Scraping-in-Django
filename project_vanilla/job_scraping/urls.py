from django.contrib import admin
from django.urls import path
from job_scraping import views
from django.conf.urls import include


urlpatterns= [
    path('admin/', admin.site.urls),
    path('',views.login,name='login'),
    path('registration/',views.registration,name='registration'),
    path('userhome/',views.userhome,name='userhome'),
    path('userlogout/',views.userlogout,name="userlogout"),
    path('listofjobs/<int:pk>/',views.Job_Detail.as_view(),name='detail'),
    path('listofjobs_sorted/<int:pk>/',views.Sorted_Job_Detail.as_view(),name='sorted_detail'),
    path('listofjobs_sorted/',views.listofjobs_sorted.as_view(),name='listofjobs_sorted'),
    path('sorting/',views.sorting,name='sorting'),
    path('listofjobs/',views.listofjobs.as_view(), name="listofjobs"),
    path('sortinginrange/',views.sortinginrange,name='sortinginrange'),
    path('listofjobs_sorted_in_range/',views.listofjobs_sorted_in_range.as_view(), name="listofjobs_sorted_in_range"),
    path('listofjobs_sorted_in_range/<int:pk>/',views.Sorted_Job_Detail_in_range.as_view(),name='Sorted_Job_Detail_in_range'),
    ]
