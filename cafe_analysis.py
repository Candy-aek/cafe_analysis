# 実行: python -m streamlit run cafe_analysis.py
# 必要ライブラリ: streamlit pandas numpy plotly openpyxl
# カフェ調査データ_2020 の集計・分析・画面表示
import streamlit as st
import re
import numpy as np
import pandas as pd

ITEMS = ['雰囲気・居心地', '清潔さ', '店内の広さ', 'テーブル・椅子', 'ネット環境', '設備(トイレ等)', '空調・換気・分煙',
         'メニューの充実', 'メニュー更新頻度', 'メニュー表の見やすさ', '商品情報の提供', '提供スピード',
         '味', '香り', '見た目', 'ボリューム', '店員の表情', '店員の挨拶・話し方', '店員の気配り', '店員の身だしなみ',
         '商品提供の丁寧さ', '価格に対する商品の質', '価格に対するサービスの質', '営業時間帯', '立地・アクセス', 'ブランドの信頼性']
Q6L = ['騒ぐ客が多い', '大声の通話が多い', '客同士のトラブル', '混雑で落ち着かない', '椅子・机がボロボロ', 'トイレが汚い',
       '店内が汚い', '広告と内容が違う', 'Wi-Fiがつながらない', '注文と違う商品', '不味くて残した', '30分以上待たされた',
       'スタッフ対応にクレーム', '商品にクレーム', '追加料金を請求されそう', '社名変更の未告知']
PUR = ['気分転換・くつろぎ', '時間調整・暇つぶし', '友人・知人との集まり', '新聞・読書', '喫煙', '仕事', '勉強',
       'ネット・動画', 'ゲーム', '朝食', '昼食', 'おやつ', '夕食', '夜食', 'その他']
BR = {36: 'コメダ珈琲店', 55: 'ドトール', 43: 'スターバックス', 38: 'サンマルクカフェ', 49: 'タリーズ', 64: 'ベローチェ',
      65: '星乃珈琲店', 5: '上島珈琲店', 32: '珈琲館', 21: 'カフェ・ド・クリエ', 29: '倉式珈琲店', 7: 'エクセルシオール',
      62: 'プロント', 67: 'マックカフェ', 72: 'むさしの森珈琲'}
SEG = {1: 'ビジネス男性', 2: 'ビジネス女性', 3: '学生', 4: 'その他'}
AGE_BINS = [0, 19, 29, 39, 49, 59, 69, 120]
AGE_LAB = ['~19歳', '20代', '30代', '40代', '50代', '60代', '70歳~']
THEMES = {
    '喫煙・分煙': r'禁煙|喫煙|タバコ|煙草|たばこ|分煙|煙|臭|匂い|におい',
    '混雑・席が取れない': r'混(?:ん|雑|み)|満席|席.{0,6}(?:ない|取れ|空いて|少な)|座れ|並ぶ|行列',
    '席・椅子・狭さ': r'狭|席の間隔|間隔|椅子|イス|ソファ|座席|座り心地|席数',
    'メニュー・味': r'メニュー|味|まずい|不味|おいしくな|美味しくな|種類|量が少な',
    'トイレ': r'トイレ|お手洗い',
    '接客・店員': r'店員|スタッフ|接客|態度|愛想|挨拶',
    'Wi-Fi・電源': r'wi-?fi|ワイファイ|ネット|コンセント|電源|充電',
    '清潔さ': r'汚|清潔|掃除|不潔|ベタベタ',
    '騒音': r'うるさ|騒|大声|話し声',
    '価格': r'高い|高め|値段|価格|値上|割高|コスパ|安く',
    '待ち時間・提供の遅さ': r'待た|待ち時間|遅|時間がかか',
    'アプリ・決済・ポイント': r'アプリ|モバイル|キャッシュレス|支払|決済|ポイント|クレジット|電子マネー|QR',
}
EMPTY = r'^(?:特に)?(?:なし|ない|無し|ありません|ございません|思いつかない)[。．.!！\s]*$'


def nps(s):
    s = pd.Series(s).dropna()
    return ((s >= 9).mean() - (s <= 6).mean()) * 100 if len(s) else np.nan


@st.cache_data(show_spinner="データを読み込んでいます…")
def load(path):
    raw = pd.read_csv(path) if str(getattr(path, 'name', path)).lower().endswith('.csv') else pd.read_excel(path, sheet_name='data')
    c = {'brand': raw['SQ6_4'].map(BR).fillna('その他ブランド'),
         'sex': raw['SQ1'].map({1: '男性', 2: '女性'}),
         'ageg': pd.cut(raw['AGE'], AGE_BINS, labels=AGE_LAB).astype(str),
         'seg': raw['FLAG2'].map(SEG),
         'sat': raw['Q1'], 'rec': raw['Q9'].replace(11, 0), 'revisit': raw['Q8_1'],
         'decl': raw['Q32_2'].ge(4).astype(float).where(raw['Q32_2'].isin([1,2,3,4,5])), 'stay': raw['Q17'], 'smoker': raw['Q31'].isin([1, 2]).astype(int),
         'q10': raw['Q10'].fillna('').astype(str), 'q22': raw['Q22'].fillna('').astype(str),}
    for i, n in enumerate(ITEMS, 1):
        c['i_' + n] = raw[f'Q2_1_{i}']
        c['w_' + n] = raw[f'Q5_1[{i}]']
    for i, n in enumerate(Q6L, 1):
        c['p_' + n] = raw[f'Q6[{i}]']
    for i, n in enumerate(PUR, 1):
        c['u_' + n] = raw[f'Q16[{i}]']
    d = pd.DataFrame(c)
    problems = d[['p_' + n for n in Q6L]]
    d['any_prob'] = (problems.sum(axis=1) > 0).astype(float).where(problems.notna().any(axis=1))
    return d


def kpi(d):
    return dict(n=len(d), sat=d.sat.mean(), nps=nps(d.rec), decl=d.decl.mean() * 100, prob=d.any_prob.mean() * 100,
                revisit=d.revisit.mean())


def group_table(d, by, min_n=1):
    g = d.groupby(by).agg(n=('sat', 'size'), 満足度=('sat', 'mean'), NPS=('rec', nps),
                          再訪意向=('revisit', 'mean'), 利用減少意向=('decl', lambda s: s.mean() * 100),
                          不満体験率=('any_prob', lambda s: s.mean() * 100))
    return g[g.n >= min_n].round(2)


def item_table(d):
    clean = d[['i_' + n for n in ITEMS] + ['sat']].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    X = clean.iloc[:, :-1].to_numpy(dtype=float)
    y = clean.sat.to_numpy(dtype=float)
    if len(y) < 28 or np.std(y) == 0:
        t = pd.DataFrame({'満足度': d[['i_' + n for n in ITEMS]].mean().values, '重視率(%)': [d['w_' + n].mean()*100 for n in ITEMS], '相関(総合満足)': np.nan, '標準化係数': np.nan, '係数(1点あたり)': np.nan}, index=ITEMS)
        return t, np.nan
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd == 0, 1, sd)
    A = np.c_[np.ones(len(y)), (X - mu) / sd]
    b = np.linalg.lstsq(A, (y - y.mean()) / y.std(), rcond=None)[0]
    r2 = 1 - ((((y - y.mean()) / y.std()) - A @ b) ** 2).sum() / len(y)
    A2 = np.c_[np.ones(len(y)), X]
    raw_b = np.linalg.lstsq(A2, y, rcond=None)[0][1:]
    t = pd.DataFrame({'満足度': X.mean(0), '重視率(%)': [d['w_' + n].mean() * 100 for n in ITEMS],
                      '相関(総合満足)': [d['i_' + n].corr(d.sat) for n in ITEMS],
                      '標準化係数': b[1:], '係数(1点あたり)': raw_b}, index=ITEMS)
    return t.round(3), r2


def problem_table(d):
    rows = []
    for n in Q6L:
        valid = d['p_' + n].isin([0, 1])
        m = d['p_' + n] == 1
        a, b = d.rec[m], d.rec[valid & ~m]
        diff = a.mean() - b.mean() if len(a) > 1 else np.nan
        se = np.sqrt(a.var() / len(a) + b.var() / len(b)) if len(a) > 1 else np.nan
        rows.append(dict(項目=n, 経験率=m[valid].mean() * 100, n=int(m.sum()), NPS_経験あり=nps(a), NPS_経験なし=nps(b),
                         NPS差=nps(a) - nps(b), 推奨度差=diff, 差の信頼区間=1.96 * se, 満足度差=d.sat[m].mean() - d.sat[valid & ~m].mean()))
    return pd.DataFrame(rows).round(2)


def theme_table(d, col):
    s = d[col]
    ok = (s.str.strip().str.len() > 0) & ~s.str.contains(EMPTY, regex=True)
    rows = [(k, int(s[ok].str.contains(p, regex=True, flags=re.I).sum())) for k, p in THEMES.items()]
    t = pd.DataFrame(rows, columns=['テーマ', '件数']).sort_values('件数', ascending=False)
    t['割合(%)'] = (t.件数 / max(ok.sum(), 1) * 100).round(1)
    return t, int(ok.sum())


def gap_matrix(d, ref, min_n=100):
    ov = ref[['i_' + n for n in ITEMS]].mean()
    rows = {}
    for b, g in d.groupby('brand'):
        if len(g) >= min_n and b != 'その他ブランド':
            rows[b] = (g[['i_' + n for n in ITEMS]].mean() - ov).values
    return pd.DataFrame(rows, index=ITEMS).T.round(2)


def purpose_table(d):
    rows = []
    for n in PUR:
        m = d['u_' + n] == 1
        if m.sum() >= 30:
            rows.append(dict(利用目的=n, 割合=m.mean() * 100, 満足度=d.sat[m].mean(), NPS=nps(d.rec[m]),
                             ネット環境=d['i_ネット環境'][m].mean(), 椅子=d['i_テーブル・椅子'][m].mean(), 空調分煙=d['i_空調・換気・分煙'][m].mean()))
    return pd.DataFrame(rows, columns=['利用目的', '割合', '満足度', 'NPS', 'ネット環境', '椅子', '空調分煙']).round(2)


import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title='カフェ利用者アンケート分析', page_icon='☕', layout='wide')
COLORS = ['#087F8C', '#D48045', '#6B66AC', '#4D9677', '#CF6574', '#456995', '#B09A43']
px.defaults.template = 'plotly_white'
px.defaults.color_discrete_sequence = COLORS
STAY = {1:'15分以内',2:'16〜30分',3:'31〜45分',4:'46〜60分',5:'61〜90分',6:'91〜120分',7:'121分以上'}
ACTION = {
'雰囲気・居心地': ('照明・音量・席の配置を見直す。まず一部の席で試す。', '居心地の評価、再訪意向'),
'清潔さ': ('客席・床の清掃時間を決め、担当者が記録する。', '清潔さの評価、汚れの指摘件数'),
'店内の広さ': ('通路と席の間隔を確認し、1人席と複数人席の配置を見直す。', '広さの評価、席に関する苦情'),
'テーブル・椅子': ('壊れた椅子を交換し、座りやすさを利用者に確認する。', '席の評価、設備の指摘件数'),
'ネット環境': ('Wi-Fiの接続を確認し、使い方と電源のある席を案内する。', 'ネット環境の評価、接続の相談件数'),
'設備(トイレ等)': ('トイレや設備を定期的に点検し、故障や汚れに対応する。', '設備の評価、故障・汚れの指摘件数'),
'空調・換気・分煙': ('空調・換気の状態を確認し、喫煙ルールを分かりやすく案内する。', '空調・換気の評価、においの指摘件数'),
'メニューの充実': ('希望する商品を追加調査し、小さな規模で新商品を試す。', 'メニューの評価、新商品の販売数'),
'メニュー更新頻度': ('季節の商品を少量で試し、注文数と廃棄量を確認する。', '更新頻度の評価、注文数、廃棄量'),
'メニュー表の見やすさ': ('文字を大きくし、価格と商品の違いを見つけやすくする。', 'メニュー表の評価、注文時の質問件数'),
'商品情報の提供': ('原材料やアレルゲンなど、必要な情報をメニューに示す。', '情報の評価、問い合わせ件数'),
'提供スピード': ('混む時間の注文から提供までの流れと人員配置を見直す。', '提供時間、提供スピードの評価'),
'味': ('作り方と提供温度をそろえ、品質を定期的に確認する。', '味の評価、作り直し件数'),
'香り': ('材料の保管と抽出方法を確認する。', '香りの評価'),
'見た目': ('盛り付けの見本を作り、提供前に確認する。', '見た目の評価'),
'ボリューム': ('量の希望を確認し、サイズを選べるか検討する。', '量の評価、残食量'),
'店員の表情': ('笑顔や声かけを練習し、忙しい時間の負担を見直す。', '接客の評価'),
'店員の挨拶・話し方': ('聞き取りやすい説明とあいさつを練習する。', '話し方の評価'),
'店員の気配り': ('案内や片付けの役割を明確にし、困っている客に声をかける。', '気配りの評価'),
'店員の身だしなみ': ('服装と衛生の確認項目をそろえる。', '身だしなみの評価'),
'商品提供の丁寧さ': ('持ち方・置き方・声かけの手順をそろえる。', '提供の評価、こぼれなどの件数'),
'価格に対する商品の質': ('価格と内容のバランスを確認し、セット商品を小規模で試す。', '商品の割安感の評価、粗利益'),
'価格に対するサービスの質': ('価格に見合う案内や接客ができているか確認する。', 'サービスの割安感の評価'),
'営業時間帯': ('時間帯別の利用数を調べ、営業時間の変更を検討する。', '営業時間の評価、人件費'),
'立地・アクセス': ('駅からの案内や入口の表示を分かりやすくする。', 'アクセスの評価'),
'ブランドの信頼性': ('商品と接客のばらつきを減らし、問題への対応をそろえる。', '信頼性の評価、再訪意向'),
}
st.markdown('''<style>
.stApp {background:#FAFAF7;color:#263D43}
.block-container {padding-top:2rem; padding-bottom:3rem;max-width:1500px}
[data-testid="stSidebar"] {background:#EDF3F1}
h1,h2,h3 {color:#244B4D;letter-spacing:.01em}
[data-testid="stMetric"] {background:white;border:1px solid #E2EAE6;border-top:4px solid #087F8C;border-radius:12px;padding:16px}
[data-testid="stMetricLabel"] {color:#50696D}
[data-testid="stMetricValue"] {color:#215E64}
[data-testid="stPlotlyChart"] {background:white;border-radius:12px}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner='初回のデータを読み込んでいます…')
def cached_load(path, mtime):
    return load(path)

@st.cache_data(show_spinner=False, max_entries=24)
def cached_items(d):
    return item_table(d)

@st.cache_data(show_spinner=False, max_entries=24)
def cached_problems(d):
    return problem_table(d)


def show(fig, reading=None, finding=None):
    fig.update_layout(font=dict(family='Meiryo, sans-serif', size=13, color='#314E54'),
                      margin=dict(l=20,r=35,t=40,b=30), paper_bgcolor='white',plot_bgcolor='white',
                      legend_title_text='', hoverlabel=dict(bgcolor='white',font_size=13))
    fig.update_xaxes(gridcolor='#EDF1EF', zerolinecolor='#BACAC5')
    fig.update_yaxes(gridcolor='#EDF1EF', zerolinecolor='#BACAC5')
    options = {'width': 'stretch'} if 'width' in __import__('inspect').signature(st.plotly_chart).parameters else {'use_container_width': True}
    st.plotly_chart(fig, config={'displaylogo':False,'scrollZoom':False}, **options)
    if reading:
        note('グラフの見方', reading)
    if finding:
        note('このグラフから分かること', finding)


def table(df):
    options = {'width': 'stretch'} if 'width' in __import__('inspect').signature(st.dataframe).parameters else {'use_container_width': True}
    st.dataframe(df, **options)


def note(title, text):
    st.markdown(f'**{title}**')
    st.write(text)


def bars(df, x, y, color=None, midpoint=None, height=520):
    args = dict(data_frame=df,x=x,y=y,orientation='h',text=x)
    if color:
        args.update(color=color,color_continuous_scale=['#CE6B56','#F3E9D8','#087F8C'])
        if midpoint is not None:
            args['color_continuous_midpoint']=midpoint
    f=px.bar(**args)
    f.update_traces(texttemplate='%{x:.2f}',textposition='outside',cliponaxis=False)
    f.update_layout(height=height,coloraxis_showscale=False)
    return f


def summary_text(d,t,pt):
    k=kpi(d)
    hi=t['満足度'].idxmax(); lo=t['満足度'].idxmin()
    common=pt.sort_values('経験率',ascending=False).iloc[0]
    note('全体の評価', f"選択した回答は{len(d):,}件です。総合満足度の平均は{k['sat']:.2f}点、また行きたい気持ちの平均は{k['revisit']:.2f}点です。どちらも10点満点です。")
    valid=d.rec.dropna(); promoter=(valid>=9).mean()*100; neutral=valid.between(7,8).mean()*100; detractor=(valid<=6).mean()*100
    note('人にすすめたい気持ち',f'9〜10点を付けた人は{promoter:.1f}%、7〜8点は{neutral:.1f}%、0〜6点は{detractor:.1f}%です。NPSは{promoter:.1f}−{detractor:.1f}＝{k["nps"]:+.1f}ポイントです。満足度と推奨度は別の質問なので、分けて確認します。')
    note('評価の高い点と低い点',f'26項目の中で、平均が最も高いのは「{hi}」（{t.loc[hi,"満足度"]:.2f}点）、最も低いのは「{lo}」（{t.loc[lo,"満足度"]:.2f}点）です。低い項目だけでなく、客が重視している割合も確認して改善の順番を考えます。')
    note('よくある不満',f'最も多い不満体験は「{common["項目"]}」で、{int(common["n"]):,}件（{common["経験率"]:.1f}%）でした。まず、この問題がいつ・どの店舗で起きるかを調べることが改善につながります。')
    note('今後の利用',f'今後の利用が「やや減る・減る」と答えた割合は{k["decl"]:.1f}%です。不満のある客だけでなく、利用が減りそうな客の理由を追加調査する必要があります。')

base=Path(__file__).resolve().parent
DATA_FILE=base/'カフェ調査データ_2020.xlsx'
if not DATA_FILE.is_file():
    files=sorted(base.glob('カフェ調査データ*.xlsx'))
    if len(files)==1:
        DATA_FILE=files[0]
    else:
        st.error('Pythonファイルと同じフォルダに「カフェ調査データ_2020.xlsx」を置いてください。')
        st.stop()
try:
    ALL=cached_load(str(DATA_FILE), DATA_FILE.stat().st_mtime_ns)
except Exception as error:
    st.error(f'Excelを読み込めませんでした。dataシートと列名を確認してください。詳細：{error}')
    st.stop()

st.sidebar.title('カフェ調査')
PAGES=['全体のまとめ','2-1 ブランド・年代の比較','2-3 項目別評価と重回帰','3-1 不満体験と自由記述','利用目的・滞在時間','改善の提案','分析方法・データの説明']
page=st.sidebar.radio('表示する分析',PAGES)
st.sidebar.divider()
with st.sidebar.form('filters'):
    st.subheader('分析する客を選ぶ')
    brand=st.multiselect('ブランド',ALL.brand.value_counts().index.tolist())
    age=st.multiselect('年代',AGE_LAB)
    seg=st.multiselect('利用者タイプ',list(SEG.values()))
    sex=st.multiselect('性別',['男性','女性'])
    st.form_submit_button('この条件で分析する',type='primary')
D=ALL.copy()
for col,selected in [('brand',brand),('ageg',age),('seg',seg),('sex',sex)]:
    if selected:
        D=D[D[col].isin(selected)]

st.title('カフェ利用者アンケート分析')
st.caption('2020年の回答から、客の評価・不満・改善の方向を調べます。')
chosen=[f'{label}：'+ '・'.join(values) for label,values in [('ブランド',brand),('年代',age),('利用者',seg),('性別',sex)] if values]
st.caption('分析対象：'+(' ／ '.join(chosen) if chosen else 'すべての回答'))
if D.empty:
    st.warning('この条件に合う回答はありません。左側の条件を変えて「この条件で分析する」を押してください。')
    st.stop()
if len(D)<100:
    st.warning(f'回答が{len(D)}件と少ないため、数値が大きく変わりやすい点に注意してください。')
k=kpi(D)
for col,(label,value) in zip(st.columns(5), [('回答数',f'{len(D):,}件'),('総合満足度 / 10点',f'{k["sat"]:.2f}'),('NPS / ポイント',f'{k["nps"]:+.1f}'),('利用が減ると思う人',f'{k["decl"]:.1f}%'),('不満を経験した人',f'{k["prob"]:.1f}%')]):
    col.metric(label,value)
st.divider()

if page=='全体のまとめ':
    st.header('評価と課題のまとめ')
    t,r2=cached_items(D); pt=cached_problems(D)
    a,b=st.columns([1,1])
    with a:
        st.subheader('総合満足度の分布')
        dist=D.sat.value_counts().reindex(range(1,11),fill_value=0).rename_axis('点数').reset_index(name='回答数')
        f=px.bar(dist,x='点数',y='回答数',color='点数',color_continuous_scale=['#D6865B','#087F8C'],text='回答数')
        f.update_layout(coloraxis_showscale=False,height=350);f.update_xaxes(dtick=1)
        mode_score=int(dist.loc[dist['回答数'].idxmax(),'点数'])
        mode_n=int(dist['回答数'].max())
        show(f, '横は満足度の点数、縦はその点数を付けた人の数です。棒が高い点数ほど、多くの人が選んでいます。',
             f'最も多い点数の1つは{mode_score}点で、{mode_n:,}件（有効回答の{mode_n/max(D.sat.count(),1)*100:.1f}%）でした。平均は{k["sat"]:.2f}点です。平均だけでなく、低い点数の回答がどのくらいあるかも確認します。')
    with b:
        st.subheader('推奨度の3つのグループ')
        valid=D.rec.dropna()
        dist=pd.DataFrame({'回答':['推奨者（9〜10点）','中立者（7〜8点）','批判者（0〜6点）'],'割合(%)':[(valid>=9).mean()*100,valid.between(7,8).mean()*100,(valid<=6).mean()*100]})
        f=px.pie(dist,names='回答',values='割合(%)',hole=.62,color='回答',color_discrete_map={dist.回答[0]:'#087F8C',dist.回答[1]:'#DCAD61',dist.回答[2]:'#CB7365'})
        f.update_layout(height=350,legend=dict(orientation='h',y=-.1))
        show(f, '円は推奨度を3つのグループに分けた割合です。9〜10点は推奨者、7〜8点は中立者、0〜6点は批判者です。',
             f'推奨者は{dist.iloc[0]["割合(%)"]:.1f}%、中立者は{dist.iloc[1]["割合(%)"]:.1f}%、批判者は{dist.iloc[2]["割合(%)"]:.1f}%です。NPSは推奨者の割合から批判者の割合を引いた{k["nps"]:+.1f}ポイントです。中立者が多い場合は、また利用する理由や人にすすめる理由を作ることが課題候補になります。')
    st.subheader('分析から分かること')
    summary_text(D,t,pt)
    st.caption('数値は選択した条件で再計算します。2020年の調査結果であり、現在の店舗の状態を示すものではありません。')

elif page=='2-1 ブランド・年代の比較':
    st.header('2-1 ブランド・年代の比較')
    st.write('ブランドや年代によって、満足度と人にすすめたい気持ちが違うかを調べます。')
    minimum=st.select_slider('比較に入れる最低回答数',options=[1,10,30,50,100,200],value=100)
    g=group_table(D,'brand',minimum).reset_index().rename(columns={'brand':'ブランド','n':'回答数'})
    chart=st.radio('ブランド比較のグラフ',['NPSの順位','満足度の順位','満足度とNPSの関係'],horizontal=True)
    if g.empty:
        st.info('最低回答数を満たすブランドがありません。最低回答数か絞り込みを変えてください。')
    else:
        if chart=='満足度とNPSの関係':
            labels=st.checkbox('ブランド名を表示',value=False)
            f=px.scatter(g,x='満足度',y='NPS',size='回答数',color='ブランド',text='ブランド' if labels else None,hover_name='ブランド',size_max=48,hover_data=['回答数','利用減少意向'])
            f.update_traces(marker=dict(line=dict(width=1,color='white')),textposition='top center')
            f.add_hline(y=0,line_dash='dot',line_color='#ABBDB6');f.update_layout(height=550)
            show(f, '右にあるブランドほど満足度が高く、上にあるほどNPSが高いことを示します。円の大きさは回答数です。',
                 f'比較対象は{len(g)}ブランドです。満足度は{g["満足度"].min():.2f}〜{g["満足度"].max():.2f}点、NPSは{g.NPS.min():+.1f}〜{g.NPS.max():+.1f}ポイントに分かれています。満足度が近くてもNPSが異なるかを見ると、「満足」と「人にすすめたい気持ち」の違いを確認できます。')
        else:
            metric='NPS' if chart=='NPSの順位' else '満足度'
            f=bars(g.sort_values(metric),metric,'ブランド',metric,0 if metric=='NPS' else None)
            if metric=='満足度': f.update_xaxes(range=[0,10.8])
            highest=g.loc[g[metric].idxmax()];lowest=g.loc[g[metric].idxmin()]
            unit='ポイント' if metric=='NPS' else '点'
            show(f, f'横の棒が右に長いほど{metric}が高いことを示します。ブランドごとに同じ指標で比較しています。',
                 f'{metric}が最も高いのは「{highest["ブランド"]}」で{highest[metric]:.2f}{unit}、低いのは「{lowest["ブランド"]}」で{lowest[metric]:.2f}{unit}です。差は{highest[metric]-lowest[metric]:.2f}{unit}です。どちらも、回答数と客の特徴を確認してから判断します。')
        best=g.loc[g.NPS.idxmax()];worst=g.loc[g.NPS.idxmin()]
        note('ブランド比較から分かること',f'比較対象の中では「{best["ブランド"]}」のNPSが最も高く{best["NPS"]:+.1f}、「{worst["ブランド"]}」が最も低く{worst["NPS"]:+.1f}でした。差は{best["NPS"]-worst["NPS"]:.1f}ポイントです。回答数が少ないブランドは変動が大きいため、回答数も一緒に確認します。')
        st.write('客の年代や利用目的がブランドごとに違うため、この差だけで店舗の優劣や原因は決められません。')
        with st.expander('ブランド別の詳しい数値'):table(g.set_index('ブランド'))
    st.subheader('年代・利用者タイプ別の比較')
    by_label=st.selectbox('比較するグループ',['年代','利用者タイプ','性別'])
    by={'年代':'ageg','利用者タイプ':'seg','性別':'sex'}[by_label]
    ag=group_table(D,by).reset_index().rename(columns={by:by_label,'n':'回答数'})
    if by=='ageg':
        ag[by_label]=pd.Categorical(ag[by_label],categories=AGE_LAB,ordered=True);ag=ag.sort_values(by_label)
    f=px.bar(ag,x=by_label,y='NPS',color=by_label,text='NPS',hover_data=['回答数','満足度','利用減少意向'])
    f.update_traces(texttemplate='%{y:.1f}',textposition='outside');f.update_layout(showlegend=False,height=400)
    show(f, f'横は{by_label}のグループ、縦はNPSです。0より上は推奨者の割合が批判者より多く、0より下は批判者の割合が多いことを示します。')
    if not ag.empty:
        hi=ag.loc[ag.NPS.idxmax()];lo=ag.loc[ag.NPS.idxmin()]
        note('グループ比較から分かること',f'NPSが高いのは「{hi[by_label]}」（{hi.NPS:+.1f}）、低いのは「{lo[by_label]}」（{lo.NPS:+.1f}）です。評価が低いグループの使い方や困りごとを調べると、改善する相手を絞れます。グループの人数が違うことにも注意が必要です。')
    table(ag.set_index(by_label))

elif page=='2-3 項目別評価と重回帰':
    st.header('2-3 何を先に改善するか')
    t,r2=cached_items(D)
    tm=t.rename_axis('項目').reset_index()
    chart=st.radio('表示するグラフ',['項目別の満足度','重視率と満足度（IPA）','総合満足度との関連（重回帰）'],horizontal=True)
    if chart=='項目別の満足度':
        show(bars(tm.sort_values('満足度'),'満足度','項目','満足度',height=840).update_xaxes(range=[0,10.8]), '棒が右に長いほど、その項目の満足度が高いことを示します。26項目を同じ1〜10点の尺度で比較します。', f'最も低い項目の1つは「{t["満足度"].idxmin()}」で{t["満足度"].min():.2f}点、最も高い項目の1つは「{t["満足度"].idxmax()}」で{t["満足度"].max():.2f}点です。低い項目は現場で理由を調べる対象になります。ただし、重視される割合と費用も合わせて改善の順番を考えます。')
    elif chart=='重視率と満足度（IPA）':
        xcut=tm['満足度'].mean(); ycut=tm['重視率(%)'].mean()
        tm['改善の目安']=np.select([(tm['満足度']<xcut)&(tm['重視率(%)']>=ycut),(tm['満足度']>=xcut)&(tm['重視率(%)']>=ycut),(tm['満足度']<xcut)&(tm['重視率(%)']<ycut)],['先に改善を検討','強みとして維持','必要性を確認'],default='維持しながら確認')
        labels=st.checkbox('すべての項目名を表示',value=False)
        f=px.scatter(tm,x='満足度',y='重視率(%)',color='改善の目安',hover_name='項目',text='項目' if labels else None,color_discrete_map={'先に改善を検討':'#D17B47','強みとして維持':'#087F8C','必要性を確認':'#8475B0','維持しながら確認':'#72968E'})
        f.update_traces(marker=dict(size=14,line=dict(width=1,color='white')),textposition='top center')
        f.add_vline(x=xcut,line_dash='dot',line_color='#A1B5AD');f.add_hline(y=ycut,line_dash='dot',line_color='#A1B5AD')
        f.update_layout(height=570,legend=dict(orientation='h',y=-.2))
        show(f, '右ほど満足度が高く、上ほどその項目を重視する人が多いことを示します。左上のオレンジ色の項目は、優先して改善を検討する候補です。',
             f'満足度の区切りは{xcut:.2f}点、重視率の区切りは{ycut:.1f}%です。左上に入る項目は{int((tm["改善の目安"]=="先に改善を検討").sum())}項目です。この区切りは26項目の平均なので、選んだ客の条件によって変わります。')
        priority=tm[tm['改善の目安']=='先に改善を検討']
        note('優先して確認したい項目','・'.join(priority.項目) if not priority.empty else 'この条件では、左上に入る項目はありません。')
    else:
        if np.isfinite(r2):
            show(bars(tm.sort_values('標準化係数'),'標準化係数','項目','標準化係数',0,height=840),
                 '標準化係数は、26項目を同時に考えたときの総合満足度との関連の目安です。正の値が大きい項目ほど、他の項目を考慮しても同じ方向の関係があります。',
                 f'最も大きい係数の1つは「{t["標準化係数"].idxmax()}」の{t["標準化係数"].max():.3f}です。総合満足度と関係する項目として確認します。係数は施策による改善効果ではなく、負の係数でもサービスを悪くすればよいとはいえません。')
            clean=D[['i_'+n for n in ITEMS]+['sat']].replace([np.inf,-np.inf],np.nan).dropna()
            n=len(clean);rank=np.linalg.matrix_rank(np.c_[np.ones(n),clean.iloc[:,:-1].to_numpy()]);p=rank-1
            adj=1-(1-r2)*(n-1)/(n-p-1) if n>p+1 else np.nan
            cols=st.columns(3);cols[0].metric('分析に使った回答',f'{n:,}件');cols[1].metric('決定係数 R²',f'{r2:.3f}');cols[2].metric('調整済み R²',f'{adj:.3f}')
            st.write('重回帰は、26項目を同時に使って総合満足度との関係を調べる方法です。係数が正で大きい項目ほど、他の項目を考慮したときに総合満足度と同じ方向の関係があります。')
            top=t['標準化係数'].nlargest(3)
            note('重回帰から分かること','係数が大きい順に、'+ '、'.join(f'「{i}」{v:.3f}' for i,v in top.items())+f'でした。この回帰式のR²は{r2:.3f}です。同じ回答データ内の総合満足度のばらつきを、どの程度説明できるかを示しています。')
            st.write('項目同士の評価が似ていると、係数が不安定になります。負の係数があっても、そのサービスを悪くすればよいとはいえません。また、係数は改善施策の効果を証明するものではありません。')
            corr=clean.iloc[:,:-1].corr(); vv=corr.abs().where(np.triu(np.ones(corr.shape),k=1).astype(bool)).stack().sort_values(ascending=False)
            if len(vv):
                pair=vv.index[0];st.caption(f'評価が最も似ている項目：{pair[0][2:]}・{pair[1][2:]}（相関 {vv.iloc[0]:.2f}）。')
        else: st.info('回答数または評価のばらつきが足りないため、この条件では重回帰を表示できません。')
    lo=t['満足度'].nsmallest(3);hi=t['満足度'].nlargest(3)
    note('項目別評価から分かること','低い項目は'+ '、'.join(f'「{i}」{v:.2f}点' for i,v in lo.items())+'です。高い項目は'+ '、'.join(f'「{i}」{v:.2f}点' for i,v in hi.items())+'です。強みを保ちながら、低評価の原因を現場で確認する必要があります。')
    with st.expander('26項目の評価・重視率・係数'): table(t)

elif page=='3-1 不満体験と自由記述':
    st.header('3-1 不満の多さと評価の違い')
    pt=cached_problems(D)
    chart=st.radio('表示するグラフ',['不満を経験した割合','不満体験とNPS差','頻度とNPS差の関係'],horizontal=True)
    if chart=='不満を経験した割合':
        show(bars(pt.sort_values('経験率'),'経験率','項目','経験率',height=650),
             '棒が右に長いほど、その不満を経験した人の割合が高いことを示します。複数の不満を選べるため、合計は100%にはなりません。',
             f'最も多い不満の1つは「{pt.loc[pt.経験率.idxmax(),"項目"]}」で{pt.経験率.max():.1f}%です。多くの客に関わる問題として、起きやすい店舗や時間帯を調べる必要があります。')
    elif chart=='不満体験とNPS差':
        show(bars(pt.sort_values('NPS差'),'NPS差','項目','NPS差',0,height=650),
             'NPS差は「経験した人のNPS − 経験していない人のNPS」です。左に長いマイナスの棒ほど、経験した人のNPSが低い傾向を示します。',
             '経験率が低い問題でも、評価の差が大きい場合があります。対応の順番は、経験者の数とNPS差を一緒に見て考えます。この比較だけでは、不満が評価低下の原因だったとは断定できません。')
    else:
        pp=pt[pt.n>0].copy(); pp['評価差']=np.where(pp.NPS差<0,'経験した人のNPSが低い','経験した人のNPSが同じか高い')
        labels=st.checkbox('すべての不満名を表示',value=False)
        f=px.scatter(pp,x='経験率',y='NPS差',size='n',size_max=48,color='NPS差',color_continuous_scale=['#BD5A55','#DEA865','#087F8C'],hover_name='項目',hover_data=['n','NPS_経験あり','NPS_経験なし'],text='項目' if labels else None)
        f.update_traces(textposition='top center',marker=dict(line=dict(width=1,color='white')));f.update_layout(height=560)
        show(f, '右ほど経験した人の割合が高く、下ほど経験した人のNPSが低い傾向があります。円の大きさは経験者の数です。',
             '右下の問題は「多く起きていて、経験者の評価も低い」ため、優先して確認する候補です。左下の問題は少数でも評価差が大きいため、見落とさずに内容を調べます。点にマウスを重ねると人数とNPSを確認できます。')
    common=pt.nlargest(1,'経験率').iloc[0]
    note('多くの人が経験している問題',f'「{common["項目"]}」が{common["経験率"]:.1f}%（{int(common["n"]):,}件）で最も多く見られます。利用する客が多い時間帯や席の使い方を調べ、広く起きる問題への対応を考えます。')
    reliable=pt[(pt.n>=20)&((len(D)-pt.n)>=20)].dropna(subset=['NPS差'])
    if not reliable.empty:
        worst=reliable.nsmallest(1,'NPS差').iloc[0]
        note('評価の差が大きい問題',f'両グループ20件以上の項目では「{worst["項目"]}」のNPS差が最も小さく{worst["NPS差"]:+.1f}ポイントでした。経験ありは{worst["NPS_経験あり"]:+.1f}、経験なしは{worst["NPS_経験なし"]:+.1f}です。発生数だけでなく、評価差も確認して対応を検討します。')
    st.write('これは異なる客同士の比較です。不満がNPS低下を引き起こしたと断定はできません。経験者の少ない項目は参考値です。')
    with st.expander('不満別の人数と詳しい数値'):table(pt.drop(columns=['差の信頼区間'],errors='ignore').set_index('項目'))
    st.subheader('自由記述でよく出る話題')
    which=st.selectbox('調べる回答',['困ったこと・改善希望（Q22）','推奨度0〜6点の理由（Q10）'])
    sub=D if which.startswith('困った') else D[D.rec<=6]
    tt,n=theme_table(sub,'q22' if which.startswith('困った') else 'q10')
    if n:
        show(bars(tt.sort_values('件数'),'件数','テーマ','件数',height=500),
             '棒が長いほど、その話題に関連する単語を含む回答が多いことを示します。1つの回答が複数の話題に入る場合があります。')
        top=tt.iloc[0]
        note('自由記述から分かること',f'「なし」などの回答を除いた{n:,}件のうち、「{top["テーマ"]}」に関連する言葉を含む回答が{int(top["件数"]):,}件（{top["割合(%)"]:.1f}%）ありました。具体的な対策を考えるための手がかりになります。')
        st.caption('単語で分類した件数です。肯定・否定や文の意味は判定していません。「におい」などの広い言葉も含むため、テーマの件数は不満の件数と一致しません。1つの回答が複数のテーマに入ります。')
        with st.expander('話題別の件数と割合'):table(tt.set_index('テーマ'))
    else:st.info('この条件では、分類できる自由記述がありません。')

elif page=='利用目的・滞在時間':
    st.header('客の使い方と評価')
    st.write('利用目的や滞在時間によって必要なサービスが違うかを確認します。')
    pu=purpose_table(D)
    if not pu.empty:
        show(bars(pu.sort_values('NPS'),'NPS','利用目的','NPS',0,height=620),
             '利用目的ごとのNPSを比べています。右に長いほど推奨者が多く、左のマイナスは批判者が多いことを示します。回答数30件以上の目的を表示しています。')
        hi=pu.loc[pu.NPS.idxmax()];lo=pu.loc[pu.NPS.idxmin()]
        note('目的別の比較から分かること',f'30件以上の回答がある利用目的では、「{hi["利用目的"]}」のNPSが{hi.NPS:+.1f}、「{lo["利用目的"]}」が{lo.NPS:+.1f}でした。仕事や勉強なら電源や静かさ、食事なら商品など、目的に合うサービスを確認することが大切です。')
        st.caption('利用目的は複数回答です。同じ人が複数のグループに含まれます。')
        table(pu.set_index('利用目的'))
    else:st.info('30件以上の回答がある利用目的はありません。')
    st.subheader('滞在時間別の比較')
    g=group_table(D,'stay').rename(index=STAY).reset_index().rename(columns={'stay':'滞在時間','n':'回答数'})
    f=px.bar(g,x='滞在時間',y='NPS',color='滞在時間',text='NPS',hover_data=['回答数','満足度']);f.update_layout(showlegend=False,height=420);f.update_traces(texttemplate='%{y:.1f}')
    show(f, '横は平均の滞在時間、縦はNPSです。滞在時間の長い客と短い客で、人にすすめたい気持ちが違うかを確認します。')
    if not g.empty:
        best=g.loc[g.NPS.idxmax()];worst=g.loc[g.NPS.idxmin()]
        note('滞在時間から分かること',f'最もNPSが高いのは「{best["滞在時間"]}」（{best.NPS:+.1f}）、低いのは「{worst["滞在時間"]}」（{worst.NPS:+.1f}）です。ただし、長く滞在させれば評価が上がるとはいえません。もともと店を気に入っている客が長く滞在している可能性もあります。')
    table(g.set_index('滞在時間'))

elif page=='改善の提案':
    st.header('分析に基づく改善の提案')
    t,_=cached_items(D);pt=cached_problems(D)
    st.write('客が重視していて、満足度が26項目の平均より低い項目から、改善を検討します。施策は実施前に店舗の状況と費用を確認します。')
    priorities=t[(t['満足度']<t['満足度'].mean())&(t['重視率(%)']>=t['重視率(%)'].mean())].sort_values('重視率(%)',ascending=False)
    if priorities.empty:
        priorities=t.nsmallest(3,'満足度');st.caption('平均基準で優先項目がなかったため、評価の低い3項目を確認します。')
    for i,(name,row) in enumerate(priorities.head(5).iterrows(),1):
        action,measure=ACTION[name]
        st.subheader(f'{i}. {name}')
        st.write(f'**根拠：** 平均{row["満足度"]:.2f}点、重視する客は{row["重視率(%)"]:.1f}%です。')
        st.write(f'**考えられる課題：** 客が求める水準と、店で受けるサービスに差がある可能性があります。実際に困っている場面を確認します。')
        st.write(f'**改善案：** {action}')
        st.write(f'**改善後に確認すること：** {measure}。実施前後を同じ質問で比べます。')
    st.subheader('不満体験への対応')
    common=pt.nlargest(1,'経験率').iloc[0]
    st.write(f'最も多い「{common["項目"]}」（{common["経験率"]:.1f}%）について、時間帯・店舗・客の使い方を記録し、起きやすい条件を確認します。そのうえで小さく対策を試し、経験率が下がるか調べます。')
    st.subheader('ブランド別に弱い項目を確認')
    g=gap_matrix(D,ALL,min_n=30)
    if not g.empty:
        selected=st.selectbox('詳しく見るブランド',g.index.tolist())
        row=g.loc[selected].nsmallest(3)
        st.caption('選択条件に合う各ブランドの評価を、絞り込み前の全回答平均と比較します。人数30件以上のブランドが対象です。')
        for name,gap in row.items():
            st.write(f'**{name}：全回答平均との差 {gap:+.2f}点**')
            st.write(ACTION[name][0])
        st.caption('平均との差が正なら、その項目は全回答平均を下回っていません。ブランド内で相対的に差が小さい項目として表示しています。')
    else:st.info('比較に必要な30件以上のブランド回答がありません。')
    st.subheader('対策を進める順番')
    st.write('① 店で起きていることを確認 → ② 一部の席や時間帯で対策を試す → ③ 評価・苦情・売上・費用を比べる → ④ 効果を確認して広げる。')
    st.write('調査だけでは、対策によって何点上がるかは分かりません。比較する店舗や期間を決めて確かめる必要があります。')

else:
    st.header('分析方法とデータの説明')
    table(pd.DataFrame([
        ['基本集計','平均・件数・割合','全体の評価と回答者の特徴を確認する'],
        ['グループ別集計','ブランド・年代・利用目的','どのグループに課題があるか調べる'],
        ['NPS','Q9の0〜10点','人にすすめたい客と、すすめにくい客の割合を比較する'],
        ['重視率と満足度（IPA）','Q2_1の26項目・Q5_1','重視されているのに評価が低い項目を探す'],
        ['重回帰','Q2_1の26項目 → Q1','複数の項目を同時に考えて、総合満足度との関連を調べる'],
        ['不満体験の比較','Q6の16項目・Q9','経験の有無で推奨度が違うか確認する'],
        ['自由記述の分類','Q22・Q10','関連する単語を数えて、よく出る話題を探す'],
    ],columns=['分析方法','使うデータ','目的']).set_index('分析方法'))
    st.subheader('数値の読み方')
    st.write('総合満足度と再訪意向は1〜10点です。NPSは、推奨度9〜10点の割合から0〜6点の割合を引きます。7〜8点は中立者です。NPSの範囲は−100〜＋100ポイントです。')
    st.write('ExcelのQ9では「11」が0点を表すため、0に直しています。利用減少意向はQ32_2の4・5、不満体験はQ6の1〜16のどれかを選んだ場合です。Q6の17は「経験なし」です。')
    st.write('平均は欠損を除いて計算します。重回帰では26項目と総合満足度がそろった回答を使います。重視率と不満経験率は、各項目に回答がある人を分母とします。')
    st.subheader('結果を見るときの注意')
    st.write('・2020年のカフェ調査です。現在の店舗やサービスの状態とは異なる可能性があります。')
    st.write('・ブランドごとに客の年齢や目的が違います。平均の差だけで、原因や店舗の優劣は決められません。')
    st.write('・相関と回帰は、関係を調べる方法です。改善施策の効果を証明するものではありません。')
    st.write('・回答数が少ないグループは値が変わりやすいため、人数も確認します。この画面では差の統計的な有意性を判定していません。')
    st.write('・自由記述は単語による分類です。文の意味や肯定・否定を自動で判断していません。')
    st.write('・「その他ブランド」は、個別名を対応付けていないブランドをまとめた分類です。1つの店舗やブランドではありません。')
