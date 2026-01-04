import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
from datetime import datetime

# タイトル
st.title("📅 シフト読み取りアプリ")
st.write("画像をアップロードすると、Googleカレンダー用のリンクを作成します。")

# APIキーの受け取り（Streamlitの「金庫」から取り出す仕組み）
# ※ここがColabと違うポイント！コードに直接キーを書かないので安全です。
try:
    api_key = st.secrets["AIzaSyDTc-i0dvaEE_iaH4G1MRCvv3KyBcTC458"]
    genai.configure(api_key=api_key)
except:
    st.error("APIキーが設定されていません。")
    st.stop()

# ユーザー設定
my_name = st.text_input("あなたの名前（シフト表の表記通りに）", "後藤")
hourly_wage = st.number_input("時給", value=1200)
year_month = st.text_input("年月（例：2026-01）", "2026-01")

# 画像アップロード
uploaded_file = st.file_uploader("シフト表の画像をアップロード", type=["jpg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロード画像', use_container_width=True)
    
    if st.button("Press Here!"):
        with st.spinner("AI is runnning now..."):
            try:
                model = genai.GenerativeModel('gemini-pro-vision')
                prompt = f"""
                この画像からシフトデータをJSONで抽出して。
                ターゲット: {my_name}
                日付は"{year_month}-01"形式。時間は"09:30"形式。
                JSONのみ出力して。
                """
                response = model.generate_content([prompt, image])
                text = response.text.replace("```json", "").replace("```", "").strip()
                if text.startswith("json"): text = text[4:]
                
                data = json.loads(text)
                st.success(f"{len(data)}件のシフトが見つかりました！")
                
                total_salary = 0
                for item in data:
                    start = datetime.strptime(f"{item['date']} {item['start']}", "%Y-%m-%d %H:%M")
                    end = datetime.strptime(f"{item['date']} {item['end']}", "%Y-%m-%d %H:%M")
                    salary = ((end - start).seconds / 3600) * hourly_wage
                    total_salary += salary
                    
                    # リンク作成
                    title = urllib.parse.quote(f"バイト({item['start']}-{item['end']})")
                    dates = start.strftime("%Y%m%dT%H%M00") + "/" + end.strftime("%Y%m%dT%H%M00")
                    url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}"
                    
                    st.markdown(f"**{item['date']}**: [カレンダーに追加]({url}) (¥{int(salary):,})")
                
                st.info(f"予想給与合計: ¥{int(total_salary):,}")
                
            except Exception as e:
                st.error(f"エラー: {e}")
