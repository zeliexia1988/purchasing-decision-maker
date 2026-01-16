import streamlit as st
import pandas as pd
from datetime import datetime

# ===============================
# 1. 页面配置与数据加载
# ===============================
st.set_page_config(page_title="Purchasing Decision Maker", layout="centered")

@st.cache_data  # 缓存数据，避免每次点击按钮都重新读取Excel，提高速度
def load_data():
    try:
        return pd.read_excel("contracts_b.xlsx")
    except Exception as e:
        st.error(f"❌ 找不到 Excel 文件 'contracts_b.xlsx'。请确保它已上传到 GitHub 仓库根目录。")
        return None

contracts = load_data()

# ===============================
# 2. 采购规则函数 (保持你的逻辑不变)
# ===============================
def rule_distributor_purchase(quantity, package, DE):
    return (package == "couronne" or DE < 125 or (DE < 200 and quantity < 1200))

def rule_contract_purchase(quantity, package, DE):
    return (
        (package == "barre" and 125 <= DE <= 200 and 1200 <= quantity)
        or (package == "barre" and 225 <= DE <= 315 and quantity < 2000)
    )

def rule_factory_purchase(quantity, package, DE):
    return (
        (package == "barre" and 315 < DE)
        or (package == "barre" and 225 <= DE <= 315 and 2000 <= quantity)
        or package.lower() == "touret"
    )

def get_contract_price_text(material, DE, PN, today, top_n=2):
    valid_contracts = contracts[
        (contracts["Material"] == material) &
        (contracts["Valid_Until"] >= today) &
        (contracts["DE"] == int(DE)) &
        (contracts["PN"] == float(PN))
    ]
    if valid_contracts.empty:
        return None

    top_sorted = valid_contracts.sort_values("Price").head(top_n)
    text = "Prix contractuel (pour référence):\n"
    for i, row in enumerate(top_sorted.itertuples(), 1):
        text += f"- Supplier {i}: {row.Supplier}, Price: {row.Price:.2f} €/ml\n"
    return text

# ===============================
# 3. 采购决策函数
# ===============================
def purchasing_decision(material, package, quantity, DE, PN):
    if contracts is None: return "Error: Data not loaded."
    today = datetime.today()

    # 1️⃣ Touret 或 厂家优先逻辑
    if package.lower() == "touret":
        result = contracts[
            (contracts["Package"].str.strip().str.lower() == "touret") &
            (contracts["Material"] == material) &
            (contracts["Valid_Until"] >= today) &
            (contracts["DE"] == int(DE)) &
            (contracts["PN"] == float(PN))
        ]
        if not result.empty:
            row = result.iloc[0]
            return f"✅ Supplier: {row['Supplier']}, Price: {row['Price']:.2f} €/ml\n\nDécision: Consultation Elydan pour confirmer: Délai de fabrication 4-6 semaines sur produit hors stock"
        else:
            return "❌ Pas de prix pour touret trouvé, contacter Category Manager Achats (Zélie XIA)"

    if rule_factory_purchase(quantity, package, DE):
        text = "💡 Decision: Consultation Fabricant sous contrat (Elydan, Centraltubi)\n"
        contract_ref = get_contract_price_text(material, DE, PN, today)
        if contract_ref:
            text += f"\n{contract_ref}\nElydan: Délai de fabrication de 4 à 6 semaines sur produit hors stock"
        else:
            text += "\n(Pas de prix contractuel pour référence, contacter Category Manager Achats (Zélie XIA))"
        return text

    # 2️⃣ 经销商优先
    if rule_distributor_purchase(quantity, package, DE):
        return "💡 Decision: Consultation Négoce"

    # 3️⃣ 合同采购
    if rule_contract_purchase(quantity, package, DE):
        valid_contracts = contracts[
            (contracts["Material"] == material) &
            (contracts["Valid_Until"] >= today) &
            (contracts["DE"] == int(DE)) &
            (contracts["PN"] == float(PN))
        ]
        if not valid_contracts.empty:
            top_sorted = valid_contracts.sort_values("Price").head(2)
            text = "✅ Decision: Application tarif contractuelle\n\n"
            for i, row in enumerate(top_sorted.itertuples(), 1):
                text += f"Supplier top{i}: {row.Supplier}, Price top{i}: {row.Price:.2f} €/ml\n"
            return text + "\nElydan : Supposé en stock, Expédition sous 72H, faire valider le délai par fournisseur"
        else:
            return "❌ Decision: Contact Category Manager Achats (Zélie XIA)"

    return "ℹ️ Decision: Contact Category Manager Achats (Zélie XIA) pour analyse spécifique."

# ===============================
# 4. Streamlit 界面构建 (替换 ipywidgets)
# ===============================
st.title("📦 Purchasing Decision Maker")
st.write("请输入采购参数以获取决策建议：")

if contracts is not None:
    # 提取选项列表
    material_list = sorted(contracts["Material"].dropna().unique().tolist())
    DE_list = sorted(contracts["DE"].dropna().unique().tolist())
    PN_list = sorted(contracts["PN"].dropna().unique().tolist())

    # 创建输入表单
    with st.container():
        material = st.selectbox("Matériau:", material_list)
        package = st.selectbox("Conditionnement:", ["couronne", "barre", "touret"])
        qty = st.number_input("Quantité (ml):", min_value=0, step=100)
        
        col1, col2 = st.columns(2)
        with col1:
            DE = st.selectbox("DE (Diamètre Extérieur):", DE_list)
        with col2:
            PN = st.selectbox("PN (Pression Nominale):", PN_list)

    st.markdown("---")

    # 运行决策按钮
    if st.button("Run Decision", type="primary"):
        result = purchasing_decision(material, package, qty, DE, PN)
        
        # 根据结果类型显示不同的颜色框
        if "❌" in result:
            st.error(result)
        elif "✅" in result:
            st.success(result)
        else:
            st.info(result)
