# coding=utf-8

from django.shortcuts import render
from django.http import HttpResponse
import json
import pymysql
from django.conf import settings

# Create your views here.

_COOKIE_NAME_OPENEDU_USER_INFO = 'openedu-user-info'
_COOKIE_NAME_EDX_USER_INFO = 'edx-user-info'


def get_connection():
    OpenEdu = settings.DATABASES['OpenEduDB']
    db = pymysql.connect(
        user = OpenEdu['USER'],
        db = OpenEdu['NAME'],
        password = OpenEdu['PASSWORD'],
        host = OpenEdu['HOST'],
        port = OpenEdu['PORT'],
    )
    return db


# 取得Email，有則回傳Email；否則回傳None
def getEmail(request):
    if request.COOKIES is not None:
        for key, value in request.COOKIES.items():
            cookie_name = key
            if cookie_name == _COOKIE_NAME_OPENEDU_USER_INFO or  cookie_name == _COOKIE_NAME_EDX_USER_INFO:
                try:
                    json_string = value
                    json_string = json_string.replace('054 ', ', ')
                    json_obj = json.dumps(json_string)
                    email = getUserEmailByUserName(json_obj['username'])
                except KeyError:
                    print('找不到username')


# 確認是否已經登入
def isLogined(request):
    if request.COOKIES is not None:
        for key in request.COOKIES.keys():
            cookiename = key
            if cookiename == _COOKIE_NAME_OPENEDU_USER_INFO or cookiename == _COOKIE_NAME_EDX_USER_INFO:
                return True
    return False


# 透過Userid取得Email
def getUserEmailById(userid):
    sql = 'SELECT email FROM edxapp.auth_user WHERE id = %s'
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, userid)
        email = cursor.fetchone()
        return email
    except Exception:
        print('Error')
    finally:
        if connection is not None:
            try:
                connection.close()
            except:
                print('Error')
    return None


# 透過UserName來取得email
def getUserEmailByUserName(username):
    sql = 'SELECT email FROM edxapp.auth_user WHERE username = %s'
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, username)
        email = cursor.fetchone()
        return email
    except Exception:
        print('Error')
    finally:
        if connection is not None:
            try:
                connection.close()
            except:
                print('Error')
    return None


# 透過Email取得UserID
def getUserIDByEmail(email):
    connection = None
    sql = 'SELECT id FROM edxapp.auth_user WHERE email = %s'

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, email)
        userid = cursor.fetchone()
        return userid
    except Exception:
        print('Error')
    finally:
        if connection is not None:
            try:
                connection.close()
            except:
                print('Error')
    return None


# 判斷是否是老師
def isTeacher(userid):
    connection = None
    sql = 'SELECT id FROM edxapp.student_courseaccessrole WHERE role = "instructor" AND user_id = %s'

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, userid)
        if cursor.fetchone():
            isteacher = True
            return isteacher
    except:
        print('Error')
    finally:
        if connection is not None:
            try:
                connection.close()
            except:
                print('Error')
    return None


# 取得老師開的課
def get_Teacher_Courses(userid):
    connection = None
    sql = 'SELECT course_id FROM edxapp.student_courseaccessrole WHERE role = "instructor" AND user_id = %s'
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, userid)
        courses = cursor.fetchall()
        return courses
    except Exception:
        print('Error')
    finally:
        if connection is not None:
            try:
                connection.close()
            except:
                print('Error')
    return None

