# -*- coding: utf-8 -*-
"""iframe 表示用の固定本文（app.py から分離・原文そのまま）。"""

HAJIMETE_PAGE_MARKDOWN = """
## 不動産鑑定評価とは？

不動産鑑定評価とは、**不動産の価値を「理由付き」で説明するための専門的な評価**です。  
単に「いくらです」と言うのではなく、「なぜその価格なのか」を文書として示します。
たとえば、銀行に担保として提出する場合や、相続で揉めないように客観的根拠を示したい場合、
裁判で説明が必要な場合など、「第三者説明」が求められる場面で利用されます。
(現在、ライブラリーズは、不動産鑑定業者登録(今後登録予定)を行っていないので、不動産の鑑定評価に関する法律の基づく鑑定評価業務は行っていません。)

## 価格はなぜブレるのか？

不動産の価格は、モノの値段のように一つに決まりにくい性質があります。  
理由は、前提条件が変わると結論が変わるからです。

例：  
- 価格時点（いつの価格か）  
- 利用状況（自用か賃貸か）  
- 権利関係（借地・借家・共有など）  
- 市場環境（金利、賃料、需給）  

ライブラリーズでは、こうした前提を整理し、誤解が起きないように“構造として”説明します。

## AIは何をしてくれるの？

AIは「勝手に価格を決める機械」ではありません。ライブラリーズにおけるAIは、不動産鑑定士の補助役です。

具体的には、  
- 公開データを整理して見やすくする  
- 前提を変えたら価格がどう動くか（感応度）を確認する  
- 外れ値や矛盾がないか（整合）を点検する  

といった“検証”を支えるために使います。  
最後に判断するのは、不動産鑑定士であり、責任も不動産鑑定士が負います。
"""

AI_TOOLS_INTRO_MARKDOWN = """
以下は **ダッシュボード**（主要ツールのショートカットカード）と **ツールカタログ** の２つから構成されています。
"""

AI_RESEARCH_GROUP_PAGE_MARKDOWN = """
## 1. 研究理念

ライブラリーズは、AIを業務効率化ツールではなく、評価構造の透明化技術と位置づけています。

AI評価研究グループは、不動産鑑定評価基準との整合を前提とした実務統合型AIモデルの研究開発拠点です。

## 2. 主要研究テーマ

(例えば)
■ AIGRAF（AI-GEO Real Estate Consulting Framework）  
■ SHAPによる価格形成要因可視化  
■ r-g構造に基づく利回り設計  
■ 補正率自動生成アルゴリズム  
■ 災害価格評価モデル  
■ ESG統合評価  

## 3. モデル構造

(例えば)
・XGBoost回帰モデル  
・SHAP分解による要因可視化  
・時系列補正指数  
・空間GIS連動  
・感応度分析統合  
"""

AI_METHODOLOGY_PAGE_MARKDOWN = """
## Role（役割）

ライブラリーズにおけるAIは、不動産鑑定士の判断を置き換えるものではありません。  
データ整理や感応度・整合の点検を通じて、判断の透明性と再現性を高めるための補助技術です。  
最終判断および説明責任は不動産鑑定士が負います。

## Use（用途）

- 公的データ・統計・事例の構造化（出所・期間・適用範囲の管理）  
- 感応度分析（前提の変化に対して価格がどう動くかの可視化）  
- 整合チェック（外れ値検出、矛盾の点検、公的価格との整合確認）  
- 説明補助（価格形成要因の構造を示し、説明責任を支援）

## Non-goals（しないこと）

- AI単独で価格を断定しません（自動査定の誤認を避けます）  
- 出所不明データを結論に採用しません  
- 前提条件の開示なしに分析結果を提示しません

## Governance（管理）

- 出所の明示：参照データの出典・期間・地域・適用範囲を記録  
- 再現性：前提条件・計算式・補正係数の開示（必要範囲）  
- 限界の明示：モデルが扱えない論点（権利関係、特殊事情等）を明文化
"""

COMPANY_OVERVIEW_PAGE_MARKDOWN = """
会社名：ライブラリーズ

代表者：磯尾 隆光

所在地：大阪府吹田市

事業内容：不動産コンサルティング業（評価・補償・訴訟・企業資産評価・収益分析 等）

設立：2026年４月

※ 現在、ライブラリーズは、不動産鑑定業者登録を行っていません。今後、不動産鑑定業者登録を予定しています。
"""

PRIVACY_PAGE_MARKDOWN = """
## 1. SDGs（持続可能な開発目標）への取り組み

ライブラリーズは、専門性と説明責任を基盤とするコンサルティング機関として、持続可能な社会の実現に貢献することを重要な責務と位置づけています。

SDGs（Sustainable Development Goals）の理念に賛同し、
不動産コンサルティング業務を通じて社会的価値の創出に取り組みます。

**主な取り組み領域**

- 多様性と包摂性の尊重（ダイバーシティの推進）  
- 健康的かつ安全な職場環境の確保（働き方の改善・安全衛生）  
- 業務運営における省エネルギーおよび環境配慮（紙資源・電力の効率化等）  
- ESG視点を踏まえた不動産評価の実施（長期価値・リスクの整理）  
- 公的評価制度の適正運用への貢献（透明性・説明可能性の向上）  

これらはスローガンに留めず、業務設計・組織運営・顧客対応の実務レベルで反映します。

---

## 2. 「個人情報の保護に関する法律」に基づく公表事項

### （1）利用目的

ライブラリーズが取得する個人情報は、以下の目的に限定して利用します。

- 不動産コンサルティング業務の遂行  
- 不動産調査・分析業務  
- お問い合わせ対応および業務連絡  
- 契約管理および報酬請求関連事務  

目的外利用は行いません。

### （2）第三者提供について

ライブラリーズは、法令に基づく場合を除き、本人の同意なく個人情報を第三者へ提供することはありません。

現時点において、オプトアウト方式による第三者提供は実施していません。

### （3）共同利用について

不動産コンサルティングに関連し、
業務の適正運用・品質確保の観点から、取引事例等の情報を共同利用する場合があります。
共同利用する情報の範囲、利用目的、共同利用者の範囲、管理責任者については、法令に基づき適切に管理します。

### （4）安全管理措置

ライブラリーズは、個人情報の漏えい、滅失、毀損を防止するため、技術的・組織的安全管理措置を講じ、継続的な見直しと改善を行います。

- アクセス権限の管理  
- 情報端末のセキュリティ対策  
- 内部管理体制の整備（ルール・教育）  
- 外部委託先がある場合の適切な監督  

---

## 3. プライバシーポリシー（基本方針）

### （1）取得方法

お問い合わせフォーム、電子メール、契約手続等により、適法かつ公正な方法で個人情報を取得します。

### （2）Cookie等の利用

本サイトでは、利便性向上およびアクセス解析のため、Cookie等の技術を使用する場合があります。

これらは個人を特定する目的では使用しません。

### （3）保管期間

個人情報は、利用目的達成に必要な期間、または法令で定められた期間保存し、期間経過後は適切な方法で消去または匿名化します。

### （4）開示・訂正・削除等の請求

本人からの開示・訂正・利用停止・削除等の請求には、法令に基づき適切に対応します。
"""

CASE_STUDIES_INTRO_MARKDOWN = """
ライブラリーズは、実績を単なる成果物一覧としてではなく、**意思決定に耐える「説明構造」の設計例**として整理します。
数値や所在地を公開できない案件であっても、思考プロセスは公開できます。
"""

# --- English companions (used when UI language is English) ---

HAJIMETE_PAGE_MARKDOWN_EN = """
## What is Real Estate Appraisal?

**Real estate appraisal** is a disciplined process to explain property value *with reasons*—not merely to state a number.  
It produces an **Appraisal Report** that a third party can review, for example for secured lending, court proceedings, audit support, or corporate governance.

*Libralys is not currently registered as a designated real estate appraisal firm under the Japanese Real Estate Appraisal Act; statutory appraisal services under that Act are therefore not provided.*

## Why do “prices” diverge?

Real property values are sensitive to **assumptions**. When assumptions change, conclusions change.

Examples:
- Valuation date (as-of date)  
- Use status (owner-occupied vs. leased)  
- Legal interests (leasehold, tenancy, co-ownership, etc.)  
- Market conditions (interest rates, rents, supply/demand)

Libralys explains value as a **traceable structure** so misunderstandings are less likely.

## What does AI do here?

AI is **not** an autonomous pricing engine. At Libralys, AI assists the **Real Property Appraiser** by:
- Structuring public data with clear sourcing and scope  
- Supporting sensitivity analysis (how value moves when assumptions change)  
- Helping detect outliers and inconsistencies  

Final judgment and accountability rest with the real property appraiser.
"""

AI_TOOLS_INTRO_MARKDOWN_EN = """
This page combines **dashboard shortcuts** (key tools) and a **tool catalog** for local demos and reference analysis.
"""

AI_RESEARCH_GROUP_PAGE_MARKDOWN_EN = """
## 1. Research philosophy

Libralys treats AI not only as an efficiency tool, but as technology that can improve **transparency of valuation structure**.

The AI valuation research group develops practice-integrated models aligned with the **Japanese Real Estate Appraisal Standards**.

## 2. Major research themes (examples)

- AIGRAF (AI–GEO Real Estate Consulting Framework)  
- SHAP-based visualization of price drivers  
- Yield design grounded in r–g structures  
- Algorithms supporting adjustment-rate workflows  
- Disaster scenario valuation models  
- ESG-integrated considerations  

## 3. Model structure (examples)

- XGBoost regression  
- SHAP decomposition for interpretability  
- Time-series adjustment indices  
- GIS-linked spatial layers  
- Integrated sensitivity analysis  
"""

AI_METHODOLOGY_PAGE_MARKDOWN_EN = """
## Role

AI at Libralys does **not** replace the judgment of a real property appraiser.  
It supports transparency and reproducibility through data organization and consistency checks.  
Final conclusions and accountability remain with the appraiser.

## Use cases

- Structuring public statistics and comparables (source, period, geography, scope)  
- Sensitivity analysis (how value responds to assumption changes)  
- Consistency checks (outliers, contradictions, reconciliation with **Official Land Price Data**)  
- Communication support (making the valuation narrative easier to follow)

## Non-goals

- No standalone “automated appraisal” claims  
- No adoption of unknown or unverifiable data as primary evidence  
- No presentation of results without explicit assumptions and limitations

## Governance

- Source transparency for all referenced data  
- Reproducibility where practicable (assumptions, methods, adjustments)  
- Explicit limitations (legal interests, special circumstances, model boundaries)
"""

COMPANY_OVERVIEW_PAGE_MARKDOWN_EN = """
**Company name:** Libralys (ライブラリーズ)

**Representative:** Takamitsu Isoo

**Location:** Suita City, Osaka Prefecture, Japan

**Business:** Real Estate Consulting (valuation support, compensation, litigation support, corporate asset valuation, **Income Analysis**, etc.)

**Established:** April 2026

*Note: Libralys is not currently registered as a designated real estate appraisal firm under the Japanese Real Estate Appraisal Act. Registration is planned for the future.*
"""

PRIVACY_PAGE_MARKDOWN_EN = """
## 1. Contribution to the SDGs

As a consulting practice built on expertise and accountability, Libralys recognizes sustainable development as a material responsibility.

**Focus areas (examples)**

- Respect for diversity and inclusion  
- Healthy and safe workplaces  
- Efficient use of energy and office resources  
- ESG-aware real estate analysis where relevant  
- Support for transparent public valuation processes  

These commitments are reflected in day-to-day operations—not only in statements.

---

## 2. Disclosures under the Act on the Protection of Personal Information (Japan)

### (1) Purposes of use

Personal information is used only for:
- Providing real estate consulting services  
- Property research and analysis  
- Responding to inquiries and routine communications  
- Contract administration and billing  

No use beyond these purposes.

### (2) Third-party provision

Except as required by law, personal information is not provided to third parties without consent.  
Opt-out third-party sharing is not used at this time.

### (3) Joint use

Where joint use is necessary for legitimate consulting operations (e.g., market evidence handling), scope, purposes, parties, and the responsible administrator are managed in accordance with applicable law.

### (4) Security measures

Libralys implements technical and organizational safeguards and reviews them on an ongoing basis, including access control, device security, internal rules and training, and supervision of processors where applicable.

---

## 3. Privacy Policy (core)

### (1) Collection

Information is collected through lawful and fair means, such as contact forms, email, and contractual processes.

### (2) Cookies

Cookies or similar technologies may be used for usability and access analytics. They are not used to identify individuals for unrelated purposes.

### (3) Retention

Data is retained only as long as necessary for the purposes of use or as required by law, then deleted or anonymized appropriately.

### (4) Requests for disclosure / correction / deletion

Requests from individuals are handled in accordance with applicable law.
"""

CASE_STUDIES_INTRO_MARKDOWN_EN = """
Libralys presents experience not as a simple list of deliverables, but as **examples of decision-grade explanatory structure**.  
Even when addresses and numbers must remain confidential, the analytical approach can still be shared transparently.
"""

SERVICES_PAGE_MARKDOWN_EN = """
## Services (overview)

Libralys provides **Real Estate Consulting** centered on **Real Estate Appraisal** thinking, **Property Price Analysis**, **Income Analysis**, and **Market Analysis**—for transactions, collateral, inheritance, leasing disputes, redevelopment, and corporate decision-making.

*Libralys is not currently registered to provide statutory appraisal services under the Japanese Real Estate Appraisal Act.*

### Reference for purchase and sale (valuation context)

Support for documenting how value is formed and explained to third parties (e.g., lenders, courts, auditors). Emphasis is placed on **Sales Comparison Approach**, **Income Capitalization Approach**, and **Cost Approach** logic, with explicit assumptions.

### Inheritance and gift valuation

Clarify as-of date, **Highest and Best Use**, and legal interests; present scenarios where needed to support family agreements and professional advisors.

### Compensation valuation

Structure loss compensation issues with clear eligibility, assumptions, and reconciliation to market evidence and applicable guidelines.

### Rent disputes and litigation support (rent opinions)

Organize issues for **Property Price Opinion** work in rent-review contexts, using multiple cross-checked methods where appropriate.

### Corporate asset valuation

Purpose-driven analyses for financial reporting, M&A, and internal governance—linking **Discounted Cash Flow (DCF) Analysis** and market evidence where relevant.

### Securitization and income-producing property

DCF-centered narratives with transparent **Capitalization Rate** / **Discount Rate** assumptions and stress views for investors, asset managers, and lenders.

### Ground rent, leasehold premia, and eviction-related settlements

Market-grounded opinions on rent levels, key money, and relocation/eviction compensation frameworks—structured for negotiation and dispute prevention.

---

For the full Japanese service sheets (including detailed technical narratives), open **“Original Japanese service descriptions”** on the Services page when the site is in English.
"""
