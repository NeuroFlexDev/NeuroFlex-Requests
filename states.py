from enum import IntEnum

class Form(IntEnum):
    NAME=0; COMPANY=1; EMAIL=2; CONTACT=3; REQ_TYPE=4; DESC=5; FILES=6; BUDGET=7; CONFIRM=8
    # ветвления
    AI_DATA=20; AI_DATASET=21
    WEB_AUTH=30; WEB_INTEGRATIONS=31
    # точечное редактирование
    EDIT_FIELD=40

class Calc(IntEnum):
    CAT=0; SCOPE=1; COMPLEXITY=2; SPEED=3; CURRENCY=4
