# -*- coding:utf-8 -*-
import radar
import random
from datetime import date
from my_app.models.standard import StandardTime
from my_app.models.timesheet import Timesheet
from my_app import db


def fake_timesheets(count=100):
    for i in range(count):
        task = StandardTime.query.get(
            random.randint(1, StandardTime.query.count()))
        timesheet = Timesheet(name=u'陈志群',
                              number=62390,
                              date=radar.random_date(start=date(year=2019,
                                                                month=10,
                                                                day=1),
                                                     stop=date(year=2019,
                                                               month=12,
                                                               day=30)),
                              airplane=unicode(str(random.randint(2760, 9999)),
                                               'utf-8'),
                              task=task.title,
                              calculated_time=task.tasktime,
                              completed=random.choice([u'全部完成', u'部分完成']),
                              belongto_team=u'<Team 胡德林>',
                              kind=task.kind,
                              approved=u'否')
        db.session.add(timesheet)
    db.session.commit()
