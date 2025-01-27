# Python Autograder
# 🛠️ 35_BA_Equinox Python Autograder

Joint project between our team from **SMU and InHeyStack**.  Developed by **Deene, Shubhash, Euan, Andrew*, Bryan, Varrya**. This Autograder is designed automate the grading process of Python assignments done in modules and courses as the sheer volume of marking combined assignments is prone to human error

---

## 🌟 **Project Overview**

The **Python Autograder System** offers the following key features:
* 📋 **Python File Grading**: 
    - AST code checking generation using rubrics, test cases, question via prompt engineering with chatGPT
    - Best practices
    - Provide suggested score, marks deducted and feedback

* ✉️ **Analytics**: 
    - Diagnostic and descriptive analytics
    - Interactive visualisations
    - Student performance overview
---

### Contributors

- [Chiang Hui Wen Deene](https://github.com/dchw248)
- [Euan Chng Zhixiang](https://github.com/theycallmeeuan)
- [Shubasheesh Prakash](https://github.com/Shubhash007)
- [Ng Kai Shen Andrew](https://github.com/andrew-nks)
- [Varrya Saxena](https://github.com/varryasaxena)
- [Lim Ming Wei Bryan](https://github.com/wrigglesmint)

---

## 🖥️ **Tech Stack**

### Frontend 
| **Technology**           | **Purpose**                                               |
|--------------------------|----------------------------------------------------------|
| ![Bootstrap](https://img.shields.io/badge/Bootstrap-HTML%2C%20CSS-563D7C?logo=bootstrap&logoColor=white) | Provides responsive design and styling for the frontend. |

### Backend 
Located in the **`/python_llm_autograder`** director

| **Technology**           | **Purpose**                                               |
|--------------------------|----------------------------------------------------------|
| ![Django](https://img.shields.io/badge/Django-MVC-092E20?logo=django&logoColor=white) | API, authentication, and business logic, database interaction|

### Database  

| **Technology**           | **Purpose**                                               |
|--------------------------|----------------------------------------------------------|
| ![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white) | The database stores all the application data, file upload paths, user autnetication

### API Tools (GPT-4o, Plotly, pandas)  
These tools are used for API interactions and data visualization.

| **Technology**           | **Purpose**                                               |
|--------------------------|----------------------------------------------------------|
| ![GPT-4o](https://img.shields.io/badge/GPT--4o-API-000000?logo=openai&logoColor=white) | One-Shot, Few-Shot LLM prompting to evaluate student solution againt model answer|
| ![Plotly](https://img.shields.io/badge/Plotly-Data%20Visualization-3F4F75?logo=plotly&logoColor=white) | Creates interactive and dynamic data visualizations.      |
| ![pandas](https://img.shields.io/badge/pandas-Data%20Analysis-150458?logo=pandas&logoColor=white) | Facilitates data manipulation and analysis.                |

---

## 🚀 **Getting Started**

### Prerequisites
Ensure the following are installed:
- Requirements file located in `cd python_llm_autograder`
```
pip install -r requirements.txt
```

---

### Database Setup

1. Create a file called `autograder.sqlite3` in python_llm_autograder directory

2. Migrate all the required tables
    ```
    python manage.py makemigrations
    python manage.py migrate
    ```
3. Create a superuser for admin purposes
    ```
    python manage.py createsuperuser
    ```

---

### Backend Setup

1. Navigate to the `/python_llm_autograder` directory.
2. Configure environment variables in the `.env` file:
   ```env
    OPENAI_ORG_ID="<openAI organisation id>"
    OPENAI_PROJECT_ID="<openAI project ID>"
    OPENAI_API_KEY="<openAI api key>"
    SECRET_KEY = "<secret key>"
    ALLOWED_HOSTS = "127.0.0.1,python-autograder.onrender.com"
    PYTHON_VERSION = "3.10.4"
    ```
    (Refer to the excel handover document for full details of all credentials)
3. Build and run the application:
   ```
   python manage.py runserver
   ```
---

## **Project Structure**

- The project is organized with Django MVC practises. 
* There is a `python_llm_autograder` project with `grading` application and `python_llm_autograder` folder with project settings.
    - `grading` contains `templates` folder and all the business logic

```plaintext
python_llm_autograder/
├── analytics/
├── grading/
│   ├── __init__.py
│   ├── admin.py        
│   ├── apps.py
│   ├── ast_generation/
│   ├── best_practises/
│   ├── dash_apps/
│   ├── forms.py
│   ├── migrations/
│   ├── models.py
│   ├── signals.py
│   ├── static/
│   ├── templates/
│   ├── templatetags/
│   ├── tests.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
├── python_llm_autograder/
│   ├── ...
├── staticfiles/
│   ├── ...
├── templates/
│   ├── ...
├── manage.py
├── autograder.sqlite3
├── requirements_mysql.txt
├── requirements.txt
├── [README.md](http://_vscodecontentref_/1)

```



## **Running in Production"
[https://python-autograder.onrender.com/](https://python-autograder.onrender.com/)
