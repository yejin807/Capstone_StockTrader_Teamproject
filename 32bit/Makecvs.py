import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import csv

from pandas import DataFrame
from pykiwoom.kiwoom import *

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        input_data = []
        input_data.clear()

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            #print(date, open, high, low, close, volume)
            input_data.append([date, open, high, low, close, volume])

        df = DataFrame(input_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        print(df)
        df.to_csv("005930.csv", index=False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    # opt10081 TR 요청
    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.set_input_value("기준일자", "20210101")
    kiwoom.set_input_value("수정주가구분", 1)
    kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")


"""
# TR 요청 (연속조회)
dfs = []
df = kiwoom.block_request("opt10081",
                          종목코드="005930",
                          기준일자="20200424",
                          수정주가구분=1,
                          output="주식일봉차트조회",
                          next=0)
print(df.head())
dfs.append(df)

while kiwoom.tr_remained:
    df = kiwoom.block_request("opt10081",
                              종목코드="005930",
                              기준일자="20200424",
                              수정주가구분=1,
                              output="주식일봉차트조회",
                              next=2)
    dfs.append(df)
    time.sleep(1)
"""
"""
trcode = "OPT10081"
rqname= "opt10081_req"
input_data = []
input_data.clear()

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)


# opt10081 TR 요청
kiwoom.SetInputValue("종목코드", "005930")
kiwoom.SetInputValue("기준일자", "20170224")
kiwoom.SetInputValue("수정주가구분", 1)
kiwoom.CommRqData(rqname, trcode, 0, "0101")

data_cnt = kiwoom.GetRepeatCnt(trcode, rqname)

for i in range(data_cnt):
    date = kiwoom.CommGetData(trcode, "", rqname, i, "일자")
    open = kiwoom.CommGetData(trcode, "", rqname, i, "시가")
    high = kiwoom.CommGetData(trcode, "", rqname, i, "고가")
    low = kiwoom.CommGetData(trcode, "", rqname, i, "저가")
    close = kiwoom.CommGetData(trcode, "", rqname, i, "현재가")
    volume = kiwoom.CommGetData(trcode, "", rqname, i, "거래량")
    input_data.append([date, open, high, low, close, volume])

df = DataFrame(input_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
print(df)
df.to_csv("005930.csv", index=False)



"""
