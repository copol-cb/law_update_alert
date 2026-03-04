import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 📧 1. 이메일 및 API 세팅
# ==========================================
SENDER_EMAIL = "wlqdldi@gmail.com" 
APP_PASSWORD = "dznoiisbzypxhsjm" 

RECEIVER_EMAILS = [
    "wlqdldi@gmail.com", 
    "chpit@naver.com"
] 

USER_ID = "wlqdldi" 
search_url = "https://www.law.go.kr/DRF/lawSearch.do"

TARGET_DATA = {
    "대기": ["대기환경보전법", "대기환경보전법 시행령", "대기환경보전법 시행규칙", "대기관리권역의 대기환경개선에 관한 특별법", "대기관리권역의 대기환경개선에 관한 특별법 시행령", "대기관리권역의 대기환경개선에 관한 특별법 시행규칙", "대기오염공정시험기준"],
    "수질": ["물환경보전법", "물환경보전법 시행령", "물환경보전법 시행규칙", "하수도법", "하수도법 시행령", "하수도법 시행규칙", "비점오염저감시설 성능검사 방법 및 절차 등에 관한 규정", "수질오염공정시험기준"],
    "폐기물": ["폐기물관리법", "폐기물관리법 시행령", "폐기물관리법 시행규칙", "사업장폐기물 배출자신고 및 처리계획 확인 업무처리지침", "음식물류 폐기물 발생 억제 계획의 수립주기 및 평가방법 등에 관한 지침", "폐기물 전자정보처리 프로그램 운영 및 사용 등에 관한 고시", "폐기물처리 현장정보의 전송방법 등에 관한 고시", "폐기물처분부담금 사무처리규정"],
    "화학물질": ["화학물질관리법", "화학물질관리법 시행령", "화학물질관리법 시행규칙", "유해화학물질의 영업허가 등에 관한 규정", "유해화학물질의 규정수량에 관한 규정", "유해화학물질별 구체적인 취급기준에 관한 규정", "유해화학물질 취급자의 개인보호장구 착용에 관한 규정", "유해화학물질 취급시설의 설치·정기·수시검사 및 안전진단의 방법 등에 관한 규정", "유해화학물질 제조·사용·저장시설 설치 및 관리에 관한 고시", "유해화학물질 소량 취급시설에 관한 고시", "유해화학물질 보관시설 설치 및 관리에 관한 고시", "화학물질의 배출량조사 및 산정계수에 관한 규정", "사고대비물질의 지정"],
    "재활용": ["자원의 절약과 재활용촉진에 관한 법률", "자원의 절약과 재활용촉진에 관한 법률 시행령", "자원의 절약과 재활용촉진에 관한 법률 시행규칙", "순환경제사회 전환 촉진법", "순환경제사회 전환 촉진법 시행령", "순환경제사회 전환 촉진법 시행규칙", "순환자원 지정 등에 관한 고시", "순환자원의 유해물질 함유 기준", "순환자원 인정 절차 및 방법 등에 관한 고시", "순환자원의 기준 및 용도에 관한 고시"],
    "기타": ["악취방지법", "악취방지법 시행령", "악취방지법 시행규칙", "소음ㆍ진동관리법", "소음ㆍ진동관리법 시행령", "소음ㆍ진동관리법 시행규칙", "잔류성오염물질 관리법", "잔류성오염물질 관리법 시행령", "잔류성오염물질 관리법 시행규칙", "환경오염피해 배상책임 및 구제에 관한 법률", "환경오염피해 배상책임 및 구제에 관한 법률 시행령", "환경오염피해 배상책임 및 구제에 관한 법률 시행규칙"]
}

# ★ [수정포인트] 검색 바보 법제처를 위한 '큰 그물' 키워드 매핑!
SHORT_QUERIES = {
    "비점오염저감계획서의 작성방법": "비점오염", # '비점오염'만 검색해서 다 쓸어옵니다.
    "비점오염저감시설 성능검사 방법 및 절차 등에 관한 규정": "비점오염"
}

# ==========================================
# 📡 2. VIP 세션(Session) 생성 및 설정
# ==========================================
session = requests.Session()
session.verify = False 
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
})

# ==========================================
# 📡 3. 법제처 서버 정밀 타격 검색! 
# ==========================================
print("📡 환경안전 전 분야 법령/행정규칙 최신 날짜를 하나씩 확인합니다... (약 20~40초 소요)")
current_dates_dict = {}

def get_target_type(name):
    if name.endswith("법") or name.endswith("법률") or name.endswith("시행령") or name.endswith("시행규칙"):
        return "law"
    return "admrul"

MAX_RETRIES = 3  

for category, items in TARGET_DATA.items():
    for item_name in items:
        clean_name = item_name.replace(" ", "")
        target_type = get_target_type(item_name)
        
        # 여기서 큰 그물 키워드를 꺼냅니다.
        query_keyword = SHORT_QUERIES.get(item_name, item_name)
        params = {"OC": USER_ID, "target": target_type, "type": "JSON", "query": query_keyword, "display": 100}
        
        for attempt in range(MAX_RETRIES):
            try:
                response = session.get(search_url, params=params, timeout=15)
                data = response.json()
                
                results = data.get("LawSearch", {}).get("law", []) if target_type == "law" else data.get("AdmRulSearch", {}).get("admrul", [])
                if isinstance(results, dict): results = [results]
                
                found = False
                for res in results:
                    res_name = res.get("법령명한글", res.get("행정규칙명", "")).replace(" ", "")
                    
                    # ★ [수정포인트] 큰 그물로 100개 가져온 뒤, 파이썬이 완벽히 똑같은 이름만 핀셋으로 집어냅니다!
                    if res_name == clean_name:
                        date = res.get("시행일자", res.get("발령일자", "알수없음"))
                        current_dates_dict[item_name] = {"category": category, "date": date}
                        found = True
                        break
                
                if not found:
                    print(f"⚠️ [{item_name}] 검색 실패 (결과 없음)")
                    current_dates_dict[item_name] = {"category": category, "date": "검색실패(결과없음)"}
                
                break 

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"🔄 [{item_name}] 서버 튕김 감지! 2초 후 {attempt + 2}차 재시도합니다...")
                    time.sleep(2) 
                else:
                    print(f"❌ [{item_name}] 3회 시도 모두 실패 (최종 에러): {e}")
                    current_dates_dict[item_name] = {"category": category, "date": "통신에러"}
        
        time.sleep(0.4) 

if len(current_dates_dict) == 0:
    print("🚨 치명적 에러: 데이터를 단 하나도 가져오지 못했습니다.")
    exit()

latest_dates_str = "|".join([f"{k}:{v['date']}" for k, v in sorted(current_dates_dict.items())])

# ==========================================
# 4. 날짜 비교 로직
# ==========================================
file_path = "last_ehs_dates.txt"
saved_dates_str = "없음"
saved_dates_dict = {}

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        saved_dates_str = f.read().strip()
        for item in saved_dates_str.split("|"):
            if ":" in item:
                k, v = item.split(":", 1)
                saved_dates_dict[k] = v

changed_items = {}
for name, info in current_dates_dict.items():
    current_date = info["date"]
    old_date = saved_dates_dict.get(name, "없음")
    
    if current_date != old_date:
        changed_items[name] = {"category": info["category"], "new_date": current_date, "old_date": old_date}

# ==========================================
# 🚨 5. 판단 및 다중 G메일 발송!
# ==========================================
if not changed_items:
    print("😴 개정된 내용이 없습니다. 조용히 퇴근합니다!")
else:
    print(f"🚨 총 {len(changed_items)}건의 개정(또는 에러) 감지! 이메일을 쏩니다!")
    
    subject = "🚨 [긴급] 환경안전(EHS) 주요 법령/규정 업데이트 알림!"
    body = "환경안전 실무 담당자님!\n법제처 서버에서 아래 규정의 개정(업데이트)이 감지되었습니다.\n\n"
    body += "변경된 법령의 원본 PDF를 다운로드하여 NotebookLM 소스를 최신화해 주세요!\n"
    body += "=" * 50 + "\n"
    
    for cat in TARGET_DATA.keys():
        cat_changed = {k: v for k, v in changed_items.items() if v["category"] == cat}
        if cat_changed:
            body += f"📘 [{cat} 분야]\n"
            for name, info in cat_changed.items():
                if info["old_date"] == "없음":
                    body += f"  - {name} (최초 등록 / 상태: {info['new_date']})\n"
                else:
                    body += f"  - {name} (🔥개정/변동됨! {info['old_date']} ➔ {info['new_date']})\n"
            body += "\n"
            
    body += "=" * 50 + "\n"
    body += "🔗 법제처 바로가기: http://www.law.go.kr/"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVER_EMAILS) 
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ 네이버를 포함한 모든 메일 주소로 알림 발송 완벽 성공!")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(latest_dates_str)
            
    except Exception as e:
        print(f"❌ 이메일 발송 중 에러가 발생했습니다: {e}")