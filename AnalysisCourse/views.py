from django.shortcuts import render
from django.db import DatabaseError, connections
from use_function import namedtuplefetchall, removeExtremum, getListAvg
from datetime import datetime, date
import json


# Create your views here.
def analysis_course_view(request):
    request.encoding = 'utf-8'
    request.GET = request.GET.copy()
    request.POST = request.POST.copy()
    to_render = {}

    if request.method == 'GET':
        to_render = doGET(request)

    if request.method == 'POST':
        to_render = doGET(request)

    return render(request, 'AnalysisCourse.html', to_render)




def doGET(request):
    RadarColumnName = ['影片觀看人數', '註冊人數', '討論區討論次數', '練習題答對率', '練習題作答率']
    mode = request.GET['mode']
    course = request.GET['course']
    dict2json = {}
    jsonArray_RegisteredPersons = []
    to_render = {}
    jsonArray_active = []
    jsonArray_answerRatio = []
    jsonArray_charter = []

    with connections['ResultDB'].cursor() as cursor:
        # course_total_data_v2 更新日期
        cursor.execute("SELECT max(統計日期) as date FROM course_total_data_v2 where 課程代碼 = %s", [course])
        result = namedtuplefetchall(cursor)

        update_course_total_data = result[-1].date

        #  取得課程基本資料
        cursor.execute(
            "SELECT 課程代碼,course_id,course_name,start_date,end_date,註冊人數,退選人數 "
            "FROM course_total_data_v2 "
            "WHERE 課程代碼 = %s and 統計日期 = %s", [course, update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        courseCode = result[-1].課程代碼
        courseId = result[-1].course_id
        courseName = result[-1].course_name
        start_date = result[-1].start_date
        end_date = result[-1].end_date
        totalRegisteredPersons = result[-1].註冊人數
        withDrew = result[-1].退選人數
        # ------------------------------------------------

        # update_video_activity 更新日期
        cursor.execute(
            "SELECT max(run_date) as max_date FROM student_total_data0912 WHERE course_id = %s", [courseId]
        )
        result = namedtuplefetchall(cursor)
        update_student_total_data = result[-1].max_date

        # update_video_activity 更新日期
        cursor.execute(
            "SELECT max(date) as max_date FROM video_activity WHERE course_id= %s", [courseId]
        )
        result = namedtuplefetchall(cursor)
        update_video_activity = result[-1].max_date

        # update_login_data 更新日期
        cursor.execute(
            "SELECT max(date) as max_date FROM login_date WHERE course_id= %s", [courseId]
        )
        result = namedtuplefetchall(cursor)
        update_login_data = result[-1].max_date

        # 統計課程的註冊人數變化
        cursor.execute(
            "SELECT count(first_login) as countFirst_login ,first_login "
            "FROM student_total_data0912 "
            "WHERE course_id= %s and run_date= %s and first_login<= %s and first_login>= %s"
            "group by first_login", [courseId, update_student_total_data, end_date, start_date]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            first_login = rs.first_login
            logincount = rs.countFirst_login
            dict2json.clear()
            dict2json['date'] = first_login
            dict2json['value'] = logincount
            jsonArray_RegisteredPersons.append(dict2json[:])
        # ----------------------------------------------------

        '''課程雷達圖'''
        # 將所有課程的練習題作答率抓出來
        all_test = []
        cursor.execute(
            "SELECT 練習題作答率  from course_total_data_v2 where 統計日期 = %s order by 練習題作答率 asc",
            [update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            all_test.append(float(rs.練習題作答率))

        # 課程總數
        totalCourceNumber = len(all_test)

        # 將所有課程的練習題答對率抓出來
        all_testCorrectPercent = []
        cursor.execute(
            "SELECT 練習題答對率  "
            "FROM course_total_data_v2 "
            "WHERE 統計日期 = %s order by 練習題答對率 asc", [update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            all_testCorrectPercent.append(float(rs.練習題答對率))

        # 將所有課程的討論區討論次數抓出來
        all_numberOfForum = []
        cursor.execute(
            "SELECT 討論區討論次數  "
            "FROM course_total_data_v2 "
            "WHERE 統計日期 = %s order by 討論區討論次數 asc", [update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            all_numberOfForum.append(int(rs.討論區討論次數))

        # 將所有課程的註冊人數抓出來
        all_registered = []
        cursor.execute(
            "SELECT 註冊人數  "
            "FROM course_total_data_v2 "
            "WHERE 統計日期 = %s order by 註冊人數 asc", [update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            all_registered.append(int(rs.註冊人數))

        # 將所有課程的影片觀看人數抓出來
        all_watchVideo = []
        cursor.execute(
            "SELECT ('影片觀看人數台灣'+'影片觀看人數_非台灣') as video "
            "FROM course_total_data_v2 "
            "WHERE 統計日期 = %s order by video asc", [update_course_total_data]
        )
        result = namedtuplefetchall(cursor)

        for rs in result:
            all_watchVideo.append(int(rs.video))

        # 將原始資料的最大值抓出來
        originalMax = [all_watchVideo[-1], all_registered[-1], all_numberOfForum[-1],
                       all_testCorrectPercent[-1], all_test[-1]]

        # 將資料去除極限值
        all_watchVideo = removeExtremum(all_watchVideo)
        all_registered = removeExtremum(all_registered)
        all_numberOfForum = removeExtremum(all_numberOfForum)
        all_testCorrectPercent = removeExtremum(all_testCorrectPercent)
        all_test = removeExtremum(all_test)

        # 將去除極限值後的最大值抓出來，即為雷達最大值
        maxRadar = [all_watchVideo[-2], all_registered[-2], all_numberOfForum[-2],
                    all_testCorrectPercent[-2], all_test[-2]]

        # 取出去除極限值後的最大值在原始資料的落點
        maxRadarSite = [all_watchVideo[-1], all_registered[-1], all_numberOfForum[-1],
                        all_testCorrectPercent[-1], all_test[-1]]

        # 取出去除極限值後的資料的平均
        avgRadar = [getListAvg(all_watchVideo), getListAvg(all_registered), getListAvg(all_numberOfForum),
                    getListAvg(all_testCorrectPercent), getListAvg(all_test)]

        # 取出該課程的資料
        cursor.execute(
            "SELECT 影片觀看人數台灣+('影片觀看人數_非台灣') as watchVideo,註冊人數 as registered, "
            "討論區討論次數 as numberOfForum,練習題答對率  as testCorrectPercent,練習題作答率 as test "
            "FROM course_total_data_v2 "
            "WHERE 統計日期= %s and 課程代碼= %s", [update_course_total_data, course]
        )
        result = namedtuplefetchall(cursor)

        RadarColumn = [result[-1].watchVideo, result[-1].registered, result[-1].numberOfForum,
                       result[-1].testCorrectPercent, result[-1].test]

        # 計算該課程除以雷達最大值的百分比
        avgRadar_percent = [0 for i in range(5)]
        RadarColumn_percent = [0 for i in range(5)]
        for i in range(len(avgRadar_percent)):
            RadarColumn_percent[i] = RadarColumn[i] / maxRadar[i] * 100
            avgRadar_percent[i] = avgRadar[i] / maxRadar[i] * 100
            if avgRadar_percent[i] > 100:
                avgRadar_percent[i] = 100
            if RadarColumn_percent[i] > 100:
                RadarColumn_percent[i] = 100

        # 將資料整理後放到 Data 準備回傳
        RadarData = []
        Data = []
        for i in range(len(avgRadar_percent)):
            Data.clear()
            Data.append(RadarColumnName[i])
            Data.append(':,'.format(originalMax[i]))
            Data.append(':,'.format(maxRadar[i]))
            Data.append(':,'.format(maxRadarSite[i] / totalCourceNumber * 100) + '%')
            Data.append(':,'.format(avgRadar[i]) + "(" + ':,'.format(avgRadar_percent[i]) + '%)')
            Data.append(':,'.format(RadarColumn[i]) + '(' + ':,'.format(RadarColumn_percent[i]) + '%)')
            RadarData.append(Data[:])
        # -----------(課程雷達圖)------------

        # 統計課程的登入人數變化
        now = datetime.now()
        time = datetime.now()

        if end_date != 'NA':
            time = datetime.strptime(end_date, '%Y-%m-%d')
            if time > now:
                time = now.strftime('%Y-%m-%d')

            cursor.execute(
                "SELECT date ,course_id,count(user_id) as count_uid "
                "FROM login_date "
                "WHERE course_id= %s and date<= %s and date>= %s group by course_id,date",
                [courseId, time, start_date]
            )
            result = namedtuplefetchall(cursor)

            jsonObject = {}
            jsonArray_temp = []
            for rs in result:
                login_date = rs.date
                loginIn = rs.count_uid
                jsonObject.clear()
                jsonObject['date'] = login_date
                jsonObject['value'] = loginIn
                jsonArray_temp.append(jsonObject)
        else:
            cursor.execute(
                "SELECT date ,course_id,count(user_id) as count_uid "
                "FROM login_date "
                "WHERE course_id= %s and date<= %s and date>= %s group by course_id,date",
                [courseId, now.strftime('%Y-%m-%d'), start_date]
            )
            result = namedtuplefetchall(cursor)

            jsonObject = {}
            jsonArray_temp = []
            for rs in result:
                login_date = rs.date
                loginIn = rs.count_uid
                jsonObject.clear()
                jsonObject['date'] = login_date
                jsonObject['value'] = loginIn
                jsonArray_temp.append(jsonObject)

        to_render['courseCode'] = courseCode
        to_render['courseId'] = courseId
        to_render['courseName'] = courseName
        to_render['start_date'] = start_date
        to_render['end_date'] = end_date

        to_render['avg_video_percent'] = avgRadar_percent[0]
        to_render['avg_registered_percent'] = avgRadar_percent[1]
        to_render['avg_countVideo_percent'] = avgRadar_percent[2]
        to_render['avg_mobile_percent'] = avgRadar_percent[3]
        to_render['avg_test_percent'] = avgRadar_percent[4]

        to_render['video_percent'] = RadarColumn_percent[0]
        to_render['registered_percent'] = RadarColumn_percent[1]
        to_render['countVideo_percent'] = RadarColumn_percent[2]
        to_render['mobile_percent'] = RadarColumn_percent[3]
        to_render['test_percent'] = RadarColumn_percent[4]

        to_render['RadarData'] = RadarData
        to_render['jsonArray_RegisteredPersons'] = json.dumps(jsonArray_RegisteredPersons)
        to_render['jsonArray_active'] = json.dumps(jsonArray_active)
        to_render['jsonArray_answerRatio'] = json.dumps(jsonArray_answerRatio)
        to_render['withDrew'] = withDrew

        to_render['jsonArray_temp'] = json.dumps(jsonArray_temp)
        to_render['jsonArray_charter'] = json.dumps(jsonArray_charter)

        to_render['totalRegisteredPersons'] = totalRegisteredPersons
        to_render['mode'] = mode
        to_render['update_course_total_data'] = update_course_total_data
        to_render['update_student_total_data'] = update_student_total_data
        to_render['update_login_data'] = update_login_data
        to_render['update_video_activity'] = update_video_activity

    return to_render
