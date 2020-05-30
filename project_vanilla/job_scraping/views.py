from django.shortcuts import render
from job_scraping.forms import UserForm, UserProfileInfoForm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from job_scraping.models import UserProfileInfo, Job_Details, Sorted_Job_Details, Sorted_in_range
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.template import RequestContext
from selenium import webdriver
from django.views.generic import ListView,DetailView
from django.utils.decorators import method_decorator
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
import time
from bs4 import BeautifulSoup
import pandas as pd

#Login Of a User- We are using django form for login of the user. In Order to authenticate, we use auth_login(request,user)
# At the same time we are storing the details of the logged in user in a csv file
def login(request):
    if request.method=='POST':
        df = pd.DataFrame(columns=('Username', 'Time'))
        uname=request.POST.get('username')
        passw=request.POST.get('password')
        #We are using the inbuilt django function of authentication
        #Note that from 'django.contrib.auth import authenticate, logout' is what we are using
        user=authenticate(username=uname,password=passw)
        timing= time.localtime(time.time())
        #We are storing it into a csv file
        csv_dict = [{'Username':uname, 'Time':timing}]
        temp_df_entry = pd.DataFrame(csv_dict)
        temp_df_entry.to_csv('login_info.csv')
        if user:
            if user.is_active:
                #After authentication-> user will be true
                auth_login(request,user)
                return HttpResponseRedirect(reverse('userhome'))
            else:
                return HttpResponse("User is inactive")
        else:
            return render(request,'job_scraping/login.html',{'err':'Invalid User Credentials!'})

    else:
        return render(request,'job_scraping/login.html')


#Here we are registering the user over here. We are using 2 model forms-> user inbuilt model ->UserProfileInfo which stored the user information
def registration(request):
    #here the form-class links the views to the form
    form_class = UserForm
    form = form_class(request.POST)
    if request.method == 'POST':
        df = pd.DataFrame(columns=('username', 'age', 'Location', 'Gender', 'Job_Interests','Qualifications'))
        # obtains the data of the request 'POST' in our form
        #This form is our inbuilt form
        form = UserForm(data=request.POST)
        #checks for implicit errors
        if form.is_valid():
            #This form refers to the user form which has only the inbuilt fields from the model
            user=form.save()
            #hash the password
            user.set_password(user.password)
            #save
            user.save()
            #For the rest of the details
            age=request.POST.get('Age')
            Location=request.POST.get('Location')
            Gender=request.POST.get('Gender')
            Job_Interests=request.POST.get('Job_Interests')
            Qualifications=request.POST.get('Qualifications')
            # creating an instance of the model
            b=UserProfileInfo.objects.create(age=age, location=Location, Gender=Gender, Job_Interests=Job_Interests, Qualifications=Qualifications, user=user)
            b.user=user
            b.save()
            #save it to a csv
            csv_dict = [{'username':user.username, 'age':age, 'Location':Location, 'Gender':Gender, 'Job_Interests':Job_Interests, 'Qualifications':Qualifications}]
            temp_df_entry = pd.DataFrame(csv_dict)
            temp_df_entry.to_csv('register.csv')
            #After registration we would want to redirect to the login page
            return HttpResponseRedirect(reverse('login'))

    #context is a dictionary instance
    #pass the userform as a context
    return render(request,'job_scraping/register.html', {'user_form':form} )



@login_required
def userhome(request):
    Job_Details.objects.all().delete()
    if request.method == "POST":
        driver = webdriver.Chrome(r"C:\Users\Dell\Desktop\chromedriver_win32\chromedriver.exe")
        driver.get('https://www.indeed.com')
        #driver.refresh()
        #This is how you get the jobs and loc from the form
        jobs = request.POST.get('job_name')
        loc = request.POST.get('city')
        print(jobs)
        print(loc)
        #Our search bars where we have to enter the job type and location
        what = driver.find_element_by_id('text-input-what')
        where = driver.find_element_by_id('text-input-where')
        #The method below is a method to send keys
        what.send_keys(Keys.CONTROL + "a")
        what.send_keys(Keys.DELETE)
        what.send_keys(jobs)
        where.send_keys(Keys.CONTROL + "a")
        where.send_keys(Keys.DELETE)
        where.send_keys(loc)
        where.submit()
        df = pd.DataFrame(columns=('Job_Title', 'Company_Name', 'Location', 'Salary', 'Job_Summary'))
        count = 0
        #We want to search for 3 pages
        while count != 3:
            print('Page :', count)
            count = count + 1
            #This gives us the page source
            source = driver.page_source
            soup = BeautifulSoup(source, 'html.parser')
            SOUP_JOBS = soup.find_all(class_= 'jobsearch-SerpJobCard unifiedRow row result clickcard')
            #We get all our jobs on the page that opens up
            iterator = 0
            for i in range(len(SOUP_JOBS)) :
                Job_Title = SOUP_JOBS[i].find(attrs={'data-tn-element' : 'jobTitle'})['title']
                print(Job_Title)
                Company_Name = SOUP_JOBS[i].find(class_ = 'company').text
                Location = SOUP_JOBS[i].find(class_ = 'location accessible-contrast-color-location').text
                print(Location)
                Salary = 'NEGOTIABLE'
                if SOUP_JOBS[i].find(class_ = 'salaryText') != None:
                    Salary = SOUP_JOBS[i].find(class_ = 'salaryText').text
                print(Salary)
                #Till here we have used the basic fundamentals of beautiful soup to extract the job name, company name,location,salary(if available)
                #Note that our job summary opens up on a new tab and hence for that we need to click on the 'a' tg associated!
                Job_Summary = ''
                index_num = iterator
                #We extract the 'href' of the 'a' tag via BeautifulSoup so that we can identify the 'a' via selenium then
                url =SOUP_JOBS[i].a['href']
                print(url)
                try:
                    #Via selenium we extract the 'a' that we are looking for
                    job= driver.find_element_by_xpath('//a[@href="'+url+'"]')
                    #We then click it to open our new tab
                    job.click()
                    print(job.text)
                except ElementClickInterceptedException:
                    #There are chances that when we open up our new tab,we witness a pop up so we close it by the method below:
                    driver.find_element_by_partial_link_text('No, thanks').click()
                    print('Pop up closed while clicking card!!')
                    job= driver.find_element_by_xpath('//a[@href="'+url+'"]')
                    #We then click it to open our new tab
                    job.click()
                    print(job.text)
                except:
                    pass

                #How to work on more than one window
                #window_handles saves references to the window handles that we have
                num_tabs = driver.window_handles
                if len(num_tabs) == 2:
                    #We switch to the second window
                    driver.switch_to_window(num_tabs[1])
                    #Extract the job summary
                    Job_Summary = driver.find_element_by_xpath("//div[@class='jobsearch-ViewJobLayout-jobDisplay icl-Grid-col icl-u-xs-span12 icl-u-lg-span7']").text
                    #Close the driver
                    driver.close()
                    try:
                        #Switch back to window 1
                        driver.switch_to_window(num_tabs[0])
                    except ElementClickInterceptedException:
                        driver.find_element_by_partial_link_text('No, thanks').click()
                        print('Pop up closed while switching back!!')
                        driver.switch_to_window(num_tabs[0])


                    if len(driver.window_handles) != 1:
                        print('OHHHHH!!! OHHHHHHHHHH!!! ERROR!!!!!!')
                        break

                else:
                    print('OHHHHH!!! OHHHHHHHHHH!!! ERROR!!!!!!')
                    break

                print(Company_Name)
                print(Job_Summary)
                #We create a data frame out of this-> basically convert from dictionary to the data frame
                csv_dict = [{'Job_Title':Job_Title, 'Company_Name':Company_Name, 'Location':Location, 'Salary':Salary, 'Job_Summary':Job_Summary}]
                temp_df_entry = pd.DataFrame(csv_dict)
                #We create an object out of it and save it in a model so that we can extract it later as per need
                b=Job_Details.objects.create(job_name=Job_Title, company_name=Company_Name, location=Location, salary=Salary, summary=Job_Summary)
                b.save()
                df = df.append(temp_df_entry, ignore_index = True)
                df.to_csv('God_Given_Gift.csv')
            try:
                #We shift to the next page
                next_page = driver.find_element_by_partial_link_text('Next ')
                next_page.click()
            except ElementClickInterceptedException:
                driver.find_element_by_partial_link_text('No, thanks').click()
                print('Pop Up Closed!!')
                next_page = driver.find_element_by_partial_link_text('Next ')
                next_page.click()
            except:
                pass
        return HttpResponseRedirect(reverse('listofjobs'))
    return render(request,'job_scraping/userhome.html')



@login_required
def userlogout(request):
    logout(request)
    #redirect the user
    return HttpResponseRedirect(reverse('login'))


#inbuilt feature of django-> allows us to list down the elements of our model
#get queryset enables you to fetch the instances from the model
#The purpose of this is to list out all jobs
@method_decorator(login_required, name='dispatch')
class listofjobs(ListView):
    model=Job_Details
    context_object_name='Job_Details'
    template_name='job_scraping/listofjobs.html'

    def get_queryset(self):
        queryset = super(listofjobs, self).get_queryset()
        return queryset

#inbuilt view of django-> sort of enables us to create dynamic views for every instace of our model
@method_decorator(login_required, name='dispatch')
class Job_Detail(DetailView):
    model=Job_Details
    context_object_name='Job_Detailing'
    template_name='job_scraping/detail.html'

#enables us to sort our results in descending order
#We use pandas for this Purpose

@login_required
#We sort the jobs in a list of jobs
def sorting(request):
    #delete any previous results
    Sorted_Job_Details.objects.all().delete()
    #Read csv details-> while getting the results we stored it in our csv
    #We retrieve information from our csv and store it in our dataframe
    #We drop the unnamed column
    df = pd.read_csv('God_Given_Gift.csv')
    df = df.drop("Unnamed: 0", axis=1)
    #Wherever the dalary is negotiable we convert it to 0 to enable conversion
    df.loc[df.Salary == 'NEGOTIABLE', 'Salary'] = 0
    Min_Salary = []
    Max_Salary = []

    #From salary column, we iterate over each salary,
    #Format of the salary is $a- $b per year/month
    for sal in df['Salary']:
        sal=str(sal)
        if sal =='0':
            Max_Salary.append(0)
            Min_Salary.append(0)

        #if we have month in our salary, then proceed
        elif 'month' in sal:
            #provided to us as range
            #Purpose is to extract the minimum and maximum salary and store it in the list
            if '-' in sal:
                start_index=sal.find('-')
                end_index=sal.find('a')
                #clean up the string
                str_final=sal[start_index+3:end_index-1]
                str_final=str_final.replace(',','')
                str_int_final=int(float(str_final))
                Max_Salary.append(str_int_final)
                Min_Salary.append(int(float(sal[2:start_index-1].replace(',',''))))
            else:
                #provided to us as absolute value
                end_index=sal.find('a')
                str_final=sal[2:end_index-1]
                str_final=str_final.replace(',','')
                str_int_final=int(float(str_final))
                Max_Salary.append(str_int_final)
                Min_Salary.append(str_int_final)


        #do the same thing, but divide it by 12 for storing it in order to handle any comparison
        elif 'year' in sal:
            if '-' in sal:
                start_index=sal.find('-')
                end_index=sal.find('a')
                str_final=sal[start_index+3:end_index-1]
                str_final=str_final.replace(',','')
                str_int_final=int(float(str_final)/12)
                Max_Salary.append(str_int_final)
                Min_Salary.append(int(float(sal[2:start_index-1].replace(',',''))/12))
            else:
                        end_index=sal.find('a')
                        str_final=sal[2:end_index-1]
                        str_final=str_final.replace(',','')
                        str_int_final=int(float(str_final)/12)
                        Max_Salary.append(str_int_final)
                        Min_Salary.append(str_int_final)

        else:
            print('Can\'t sort, LOL!')

    #Add these 2 rows to the dataframe
    df['Min_Salary'] = Min_Salary
    df['Max_Salary'] = Max_Salary
    #Sort according to maximum salary
    df.sort_values('Max_Salary', ascending=False, inplace=True)
    print(df)

    #Create a new model, with the following order of the sorted jobs
    for i in range(0,df.shape[0]):
        b=Sorted_Job_Details.objects.create(job_name=df.iloc[i][0], company_name=df.iloc[i][1], location=df.iloc[i][2], salary=df.iloc[i][3], summary=df.iloc[i][4])
        b.save()
    return render(request,'job_scraping/intermediate.html')



#This is in order to find jobs in a particular range
def sortinginrange(request):
    if request.method=='POST':
        max_salary=request.POST.get('max_salary')
        min_salary=request.POST.get('min_salary')
        Sorted_in_range.objects.all().delete()
        df = pd.read_csv('God_Given_Gift.csv')
        df = df.drop("Unnamed: 0", axis=1)
        df.loc[df.Salary == 'NEGOTIABLE', 'Salary'] = 0
        Min_Salary = []
        Max_Salary = []

        for sal in df['Salary']:
            sal=str(sal)

            if sal =='0':
                Max_Salary.append(0)
                Min_Salary.append(0)

            elif 'month' in sal:
                if '-' in sal:
                    start_index=sal.find('-')
                    end_index=sal.find('a')

                    str_final=sal[start_index+3:end_index-1]
                    str_final=str_final.replace(',','')
                    str_int_final=int(float(str_final))

                    Max_Salary.append(str_int_final)
                    Min_Salary.append(int(float(sal[2:start_index-1].replace(',',''))))

                else:
                    end_index=sal.find('a')
                    str_final=sal[2:end_index-1]
                    str_final=str_final.replace(',','')
                    str_int_final=int(float(str_final))
                    Max_Salary.append(str_int_final)
                    Min_Salary.append(str_int_final)


            elif 'year' in sal:
                if '-' in sal:
                    start_index=sal.find('-')
                    end_index=sal.find('a')
                    str_final=sal[start_index+3:end_index-1]
                    str_final=str_final.replace(',','')
                    str_int_final=int(float(str_final)/12)
                    Max_Salary.append(str_int_final)
                    Min_Salary.append(int(float(sal[2:start_index-1].replace(',',''))/12))
                else:
                            end_index=sal.find('a')
                            str_final=sal[2:end_index-1]
                            str_final=str_final.replace(',','')
                            str_int_final=int(float(str_final)/12)
                            Max_Salary.append(str_int_final)
                            Min_Salary.append(str_int_final)

            else:
                print('Can\'t sort, LOL!')

        df['Min_Salary'] = Min_Salary
        df['Max_Salary'] = Max_Salary
        min_salary=int(min_salary)
        max_salary=int(max_salary)

        #Create a new dataframe containg those items which match ur comparisons
        Suitable_jobs = df[(df['Min_Salary'] >= min_salary) & (df['Max_Salary'] <= max_salary)]
        #Create a new model for the same purpose
        #Shape gives us the length and breadth which is required
        for i in range(0,Suitable_jobs.shape[0]):
            b=Sorted_in_range.objects.create(job_name=Suitable_jobs.iloc[i][0], company_name=Suitable_jobs.iloc[i][1], location=Suitable_jobs.iloc[i][2], salary=Suitable_jobs.iloc[i][3], summary=Suitable_jobs.iloc[i][4])
            b.save()

        return render(request,'job_scraping/intermediate_range.html',{'form_bool':'yes'})

    return render(request,'job_scraping/intermediate_range.html')


@method_decorator(login_required, name='dispatch')
class Sorted_Job_Detail(DetailView):
    model=Sorted_Job_Details
    context_object_name='Job_Detailing'
    template_name='job_scraping/sorted_detail.html'



@method_decorator(login_required, name='dispatch')
class listofjobs_sorted(ListView):
    model=Sorted_Job_Details
    context_object_name='Sorted_Job_Details'
    template_name='job_scraping/listofjobs_sorted.html'

    def get_queryset(self):
        queryset = super(listofjobs_sorted, self).get_queryset()
        return queryset


@method_decorator(login_required, name='dispatch')
class Sorted_Job_Detail_in_range(DetailView):
    model= Sorted_in_range
    context_object_name='Job_Detailing'
    template_name='job_scraping/Sorted_detail_range.html'



@method_decorator(login_required, name='dispatch')
class listofjobs_sorted_in_range(ListView):
    model=Sorted_in_range
    context_object_name='Sorted_Job_Details'
    template_name='job_scraping/listofjobs_sorted_in_range.html'

    def get_queryset(self):
        queryset = super(listofjobs_sorted_in_range, self).get_queryset()
        return queryset
