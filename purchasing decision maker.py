# 安装必要库

import pandas as pd
from datetime import datetime
from ipywidgets import Dropdown, IntText, VBox, Output, Button
from IPython.display import display

# ===============================
# 读取合同 Excel
# ===============================
contracts = pd.read_excel("contracts_b.xlsx")

# ===============================
# 采购规则函数
# ===============================
def rule_distributor_purchase(quantity, package, DE):
    return (
        package == "couronne"
        or DE < 125
        or (DE < 200 and quantity < 1200)
    )

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

# ===============================
# 获取合同价格
# ===============================
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

    text = "Prix contractuel (pour reference):\n"
    for i, row in enumerate(top_sorted.itertuples(), 1):
        text += (
            f"- Supplier {i}: {row.Supplier}, "
            f"Price: {row.Price:.2f} €/ml\n"
        )

    return text
# ===============================
# 采购决策函数
# ===============================
def purchasing_decision(material, package, quantity, DE, PN):
    today = datetime.today()

    # 输入校验
    if not material: return "❗ Please select a material."
    if not package: return "❗ Please select a package."
    if quantity is None: return "❗ Please enter quantity."
    if DE is None: return "❗ Please enter DE (Diamètre Extérieur)."
    if PN is None: return "❗ Please enter PN (Pression Nominale)."

    text = ""

    # 1️⃣ Touret 或厂家优先
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
                price = row["Price"]
                supplier = row["Supplier"]
                return f" Supplier: {supplier}, Price: {price:.2f} €/ml\n Décision: Consultation Elydan pour confirmer: Délai de fabrication 4-6 semaines sur produit hors stock"
            else: 
                return "Pas de prix pour touret trouvé, contacter Category Manager Achats (Zélie XIA)"
     
    if rule_factory_purchase(quantity, package=package, DE=DE):
        text = "Decision: Consultation Fabricant sous contrat (Elydan, Centraltubi)\n" 
        contract_ref = get_contract_price_text(material, DE, PN, today)
        if contract_ref:
            text += "\n" + contract_ref + "\n" + "Elydan: Délai de fabrication de 4 à 6 semaines sur produit hors stock"
        else:
            text += "\n(Pas de prix contracutel pour référence, contacter Category Manager Achats (Zélie XIA))"
        return text 

    # 2️⃣ 经销商优先
    if rule_distributor_purchase(quantity, package, DE):
        return "Decision: Consultation Négoce"

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
            text = "Decision: Application tarif contractuelle\n"
            for i, row in enumerate(top_sorted.itertuples(), 1):
                text +=(
                    f"Supplier top{i}: {row.Supplier}, "
                    f"Price top{i}: {row.Price:.2f} €/ml\n"
                )
            return text + "Elydan : Supposé en stock, Expédition sous 72H, faire valider le délai par fournisseur"
    else: 
            return "Decision: Contact Category Manager Achats (Zélie XIA)"
      
  

# ===============================
# Colab 控件界面
# ===============================
material_list = sorted(contracts["Material"].dropna().unique().tolist())
DE_list = sorted(contracts["DE"].dropna().unique().tolist())
PN_list = sorted(contracts["PN"].dropna().unique().tolist())

material_w = Dropdown(options=material_list, description="Matériau:", value=None)
package_w = Dropdown(options=["couronne", "barre", "touret"], description="Conditionnement:", value=None)
qty_w = IntText(description="Quantité(ml):")
DE_w = Dropdown(options=DE_list, description="DE:", value=None)
PN_w = Dropdown(options=PN_list, description="PN:", value=None)

run_btn = Button(description="Run Decision", button_style="success")
out = Output()

def on_run_clicked(b):
    out.clear_output()
    with out:
        result = purchasing_decision(
            material_w.value,
            package_w.value,
            qty_w.value,
            DE_w.value,
            PN_w.value
        )
        print(result)

run_btn.on_click(on_run_clicked)

display(VBox([material_w, package_w, qty_w, DE_w, PN_w, run_btn, out]))
