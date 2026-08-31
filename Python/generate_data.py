import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# Reproducibility - same "random" data every time you run it
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

# Make an output folder for our CSVs
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Dim_Date ----------

start_date = datetime(2025, 1, 1)
end_date = datetime(2026, 8, 29)  # last date orders are generated for

# Dim_Date needs to extend further than orders, to cover ship/delivery dates
# Max delay: 5 days ship + 7 days delivery = 12 days buffer, rounded up for safety
dim_date_end = end_date + timedelta(days=20)

date_list = pd.date_range(start=start_date, end=dim_date_end, freq='D')

dim_date = pd.DataFrame({'Date': date_list})

dim_date['DateKey'] = dim_date['Date'].dt.strftime('%Y%m%d').astype(int)
dim_date['Year'] = dim_date['Date'].dt.year
dim_date['Month'] = dim_date['Date'].dt.month
dim_date['MonthName'] = dim_date['Date'].dt.strftime('%B')
dim_date['Day'] = dim_date['Date'].dt.day
dim_date['DayOfWeek'] = dim_date['Date'].dt.strftime('%A')
dim_date['IsWeekend'] = dim_date['Date'].dt.dayofweek >= 5
dim_date['Quarter'] = dim_date['Date'].dt.quarter
dim_date['Week'] = dim_date['Date'].dt.isocalendar().week

# Fiscal year: April-March (common in SAP/Indian business context)
# If month is Jan-Mar, fiscal year = calendar year (year started last April)
# If month is Apr-Dec, fiscal year = calendar year + 1 (next April starts new FY)
dim_date['FiscalYear'] = np.where(
    dim_date['Month'] <= 3,
    dim_date['Year'],
    dim_date['Year'] + 1
)

# Fiscal period: April = period 1, May = period 2, ... March = period 12
dim_date['FiscalPeriod'] = np.where(
    dim_date['Month'] <= 3,
    dim_date['Month'] + 9,   # Jan(1)->10, Feb(2)->11, Mar(3)->12
    dim_date['Month'] - 3    # Apr(4)->1, May(5)->2, ... Dec(12)->9
)

# Reorder columns nicely
dim_date = dim_date[['DateKey', 'Date', 'Year', 'Quarter', 'Month', 'MonthName',
                      'Day', 'Week', 'DayOfWeek', 'IsWeekend', 'FiscalYear', 'FiscalPeriod']]

dim_date.to_csv(os.path.join(DATA_DIR, "Dim_Date.csv"), index=False)
print("Dim_Date created:", dim_date.shape)

# ---------- Dim_Warehouse ----------

warehouses = [
    {'WarehouseID': 1, 'WarehouseName': 'Mumbai',    'Region': 'West',  'City': 'Mumbai',    'SizeSqft': 45000, 'Tier': 'Tier 1'},
    {'WarehouseID': 2, 'WarehouseName': 'Delhi',     'Region': 'North', 'City': 'Delhi',     'SizeSqft': 38000, 'Tier': 'Tier 1'},
    {'WarehouseID': 3, 'WarehouseName': 'Bangalore', 'Region': 'South', 'City': 'Bangalore', 'SizeSqft': 32000, 'Tier': 'Tier 1'},
    {'WarehouseID': 4, 'WarehouseName': 'Kolkata',   'Region': 'East',  'City': 'Kolkata',   'SizeSqft': 22000, 'Tier': 'Tier 2'},
    {'WarehouseID': 5, 'WarehouseName': 'Pune',      'Region': 'West',  'City': 'Pune',      'SizeSqft': 18000, 'Tier': 'Tier 2'},
]

dim_warehouse = pd.DataFrame(warehouses)

dim_warehouse.to_csv(os.path.join(DATA_DIR, "Dim_Warehouse.csv"), index=False)
print("Dim_Warehouse created:", dim_warehouse.shape)

# ---------- Dim_Client ----------

client_names = [
    'Nova Apparel', 'Zenith Electronics', 'Bloom Beauty Co', 'Peak Performance Gear',
    'Urban Nest Home', 'Sprout Organics', 'Velocity Sports', 'Lumen Lighting',
    'Craftline Furniture', 'Pixel Gadgets', 'Terra Kitchenware', 'Aria Fashion'
]

tiers = ['Enterprise', 'Enterprise', 'Mid', 'Mid', 'Mid', 'SMB', 'SMB', 'SMB', 'SMB', 'Mid', 'Enterprise', 'SMB']
industries = ['Apparel', 'Electronics', 'Beauty', 'Sports', 'Home Goods', 'Food & Grocery',
              'Sports', 'Home Goods', 'Furniture', 'Electronics', 'Kitchenware', 'Apparel']

dim_client = pd.DataFrame({
    'ClientID': range(1, len(client_names) + 1),
    'ClientName': client_names,
    'ClientTier': tiers,
    'Industry': industries
})

# Give each client a random onboarding date sometime in the first 6 months of our date range
onboard_start = datetime(2025, 1, 1)
onboard_end = datetime(2025, 6, 30)
onboard_range_days = (onboard_end - onboard_start).days

dim_client['OnboardedDate'] = [
    onboard_start + timedelta(days=random.randint(0, onboard_range_days))
    for _ in range(len(dim_client))
]

dim_client.to_csv(os.path.join(DATA_DIR, "Dim_Client.csv"), index=False)
print("Dim_Client created:", dim_client.shape)

# ---------- Dim_SKU ----------

categories_info = {
    'Apparel':       {'cost_range': (200, 800),   'margin_range': (0.35, 0.55)},
    'Electronics':   {'cost_range': (500, 5000),  'margin_range': (0.10, 0.25)},
    'Beauty':        {'cost_range': (100, 600),   'margin_range': (0.40, 0.60)},
    'Home Goods':    {'cost_range': (300, 2000),  'margin_range': (0.25, 0.40)},
    'Sports':        {'cost_range': (400, 3000),  'margin_range': (0.20, 0.35)},
    'Kitchenware':   {'cost_range': (200, 1500),  'margin_range': (0.25, 0.40)},
    'Furniture':     {'cost_range': (1000, 8000), 'margin_range': (0.15, 0.30)},
}

sku_rows = []
sku_id = 1

for category, info in categories_info.items():
    num_skus = random.randint(6, 9)   # 6-9 SKUs per category, adds up to ~50-60
    for _ in range(num_skus):
        unit_cost = round(random.uniform(*info['cost_range']), 2)
        margin = random.uniform(*info['margin_range'])
        # Price is derived from cost + margin, not made up separately -
        # keeps cost/price relationship realistic per category
        unit_price = round(unit_cost / (1 - margin), 2)

        sku_rows.append({
            'SKUID': sku_id,
            'ProductName': f"{category} Item {sku_id}",
            'Category': category,
            'UnitCost': unit_cost,
            'UnitPrice': unit_price
        })
        sku_id += 1

dim_sku = pd.DataFrame(sku_rows)

dim_sku.to_csv(os.path.join(DATA_DIR, "Dim_SKU.csv"), index=False)
print("Dim_SKU created:", dim_sku.shape)

# ---------- Dim_CostType ----------

cost_types = [
    {'CostTypeID': 1, 'CostTypeName': 'Labor'},
    {'CostTypeID': 2, 'CostTypeName': 'Storage'},
    {'CostTypeID': 3, 'CostTypeName': 'Packaging'},
    {'CostTypeID': 4, 'CostTypeName': 'Last-Mile Shipping'},
    {'CostTypeID': 5, 'CostTypeName': 'Returns Processing'},
]

dim_costtype = pd.DataFrame(cost_types)

dim_costtype.to_csv(os.path.join(DATA_DIR, "Dim_CostType.csv"), index=False)
print("Dim_CostType created:", dim_costtype.shape)

# ---------- Fact_Orders: setup ----------

order_rows = []
order_id = 1

client_ids = dim_client['ClientID'].tolist()
sku_ids = dim_sku['SKUID'].tolist()
warehouse_ids = dim_warehouse['WarehouseID'].tolist()

sku_lookup = dim_sku.set_index('SKUID').to_dict('index')
client_onboard_lookup = dim_client.set_index('ClientID')['OnboardedDate'].to_dict()

order_date_list = pd.date_range(start=start_date, end=end_date, freq='D')
cost_type_ratios = {1: 0.35, 2: 0.20, 3: 0.15, 4: 0.25, 5: 0.05}  # Labor, Storage, Packaging, Shipping, Returns

print("Setup done")
print("Clients:", client_ids)
print("Warehouses:", warehouse_ids)
print("Number of SKUs:", len(sku_ids))

# ---------- Fact_Orders: generate orders ----------

for date in order_date_list:
    month = date.month
    seasonal_multiplier = 1.0
    if month in [10, 11]:
        seasonal_multiplier = 1.8
    elif month in [12, 1]:
        seasonal_multiplier = 1.4
    elif month in [6, 7]:
        seasonal_multiplier = 0.7

    if date.dayofweek >= 5:
        seasonal_multiplier *= 0.6

    base_orders_per_day = 40
    num_orders_today = int(np.random.poisson(base_orders_per_day * seasonal_multiplier))

    for _ in range(num_orders_today):
        client_id = random.choice(client_ids)
        if date < client_onboard_lookup[client_id]:
            continue

        sku_id = random.choice(sku_ids)
        sku_info = sku_lookup[sku_id]

        warehouse_id = random.choices(warehouse_ids, weights=[25, 22, 22, 16, 15])[0]

        qty = random.randint(1, 5)
        revenue = round(sku_info['UnitPrice'] * qty, 2)
        cogs = round(sku_info['UnitCost'] * qty, 2)

        # Give each non-Kolkata warehouse a slightly different baseline efficiency,
        # so they look like independent real warehouses instead of clones
        warehouse_base_rates = {1: 0.15, 2: 0.20, 3: 0.17, 4: 0.25, 5: 0.19}  # Mumbai, Delhi, Bangalore, Kolkata, Pune
        base_fulfillment_rate = warehouse_base_rates[warehouse_id]
        fulfillment_cost = round(revenue * base_fulfillment_rate * random.uniform(0.85, 1.15), 2)

        ship_delay = random.choices([1, 2, 3, 5], weights=[60, 25, 10, 5])[0]
        ship_date = date + timedelta(days=ship_delay)
        delivery_delay = random.choices([2, 3, 4, 7], weights=[50, 30, 15, 5])[0]
        delivery_date = ship_date + timedelta(days=delivery_delay)

        # Promised delivery date is based on client tier SLA - a real business commitment,
        # not an arbitrary cutoff. Enterprise clients get faster contractual SLAs.
        client_tier = dim_client.loc[dim_client['ClientID'] == client_id, 'ClientTier'].values[0]
        sla_days_by_tier = {'Enterprise': 5, 'Mid': 6, 'SMB': 7}
        sla_days = sla_days_by_tier[client_tier]
        promised_delivery_date = date + timedelta(days=sla_days)

        order_rows.append({
            'OrderID': order_id,
            'DateKey': int(date.strftime('%Y%m%d')),
            'ClientID': client_id,
            'SKUID': sku_id,
            'WarehouseID': warehouse_id,
            'Quantity': qty,
            'Revenue': revenue,
            'COGS': cogs,
            'FulfillmentCost': fulfillment_cost,
            'OrderDate': date,
            'ShipDate': ship_date,
            'DeliveryDate': delivery_date,
            'PromisedDeliveryDate': promised_delivery_date
        })
        order_id += 1

fact_orders = pd.DataFrame(order_rows)
fact_orders.to_csv(os.path.join(DATA_DIR, "Fact_Orders.csv"), index=False)
print("Fact_Orders created:", fact_orders.shape)

# ---------- Fact_Inventory_Snapshot ----------

inventory_rows = []

# Sample dates to keep file size reasonable - one snapshot per week per SKU/warehouse
snapshot_dates = pd.date_range(start=start_date, end=end_date, freq='W')

for warehouse_id in warehouse_ids:
    for sku_id in sku_ids:
        # Each SKU/warehouse combo starts with a random baseline stock level
        stock = random.randint(50, 500)
        for snap_date in snapshot_dates:
            # Random walk: stock drifts down (sales) then jumps up (restock)
            change = random.randint(-40, 15)
            stock = max(0, stock + change)
            if stock < 30:
                stock += random.randint(100, 300)  # restock trigger

            inventory_rows.append({
                'DateKey': int(snap_date.strftime('%Y%m%d')),
                'WarehouseID': warehouse_id,
                'SKUID': sku_id,
                'StockOnHand': stock
            })

fact_inventory = pd.DataFrame(inventory_rows)
fact_inventory.to_csv(os.path.join(DATA_DIR, "Fact_Inventory_Snapshot.csv"), index=False)
print("Fact_Inventory_Snapshot created:", fact_inventory.shape)

# ---------- Budget ----------

budget_rows = []

# Monthly budget periods across our date range
budget_months = pd.date_range(start=start_date, end=end_date, freq='MS')  # MS = month start

# First, calculate actual average monthly revenue per warehouse from Fact_Orders
# This makes the budget grounded in real performance, not disconnected random numbers
fact_orders_temp = pd.DataFrame(order_rows)
fact_orders_temp['MonthStart'] = fact_orders_temp['OrderDate'].values.astype('datetime64[M]')
monthly_actuals = fact_orders_temp.groupby(['WarehouseID', 'MonthStart'])['Revenue'].sum().reset_index()
avg_monthly_by_warehouse = monthly_actuals.groupby('WarehouseID')['Revenue'].mean().to_dict()

for month_start in budget_months:
    for warehouse_id in warehouse_ids:
        # Base target on actual average performance for that warehouse, with controlled variance
        # so some months beat target and some miss it - a believable budget, not a random guess
        base_target = avg_monthly_by_warehouse.get(warehouse_id, 800000)
        # Wider variance for a more realistic mix of over/under performance
        # Occasionally a warehouse has a genuinely rough or strong month, not just mild noise
        variance_roll = random.random()
        if variance_roll < 0.2:
            # 20% chance of a rough month - target set noticeably higher than what was achieved
            multiplier = random.uniform(1.10, 1.30)
        elif variance_roll < 0.4:
            # 20% chance of a strong month - target set noticeably lower
            multiplier = random.uniform(0.75, 0.90)
        else:
            # 60% of months - normal variance, close to target either way
            multiplier = random.uniform(0.90, 1.10)

        target_revenue = round(base_target * multiplier, 2)
        target_cost_pct = 0.18  # target is always 18% - this is what warehouse 4 will miss

        budget_rows.append({
            'DateKey': int(month_start.strftime('%Y%m%d')),
            'WarehouseID': warehouse_id,
            'TargetRevenue': target_revenue,
            'TargetCostPct': target_cost_pct
        })

budget = pd.DataFrame(budget_rows)
budget.to_csv(os.path.join(DATA_DIR, "Budget.csv"), index=False)
print("Budget created:", budget.shape)

# ---------- Fact_Order_Costs ----------

cost_rows = []
cost_type_ids = list(cost_type_ratios.keys())

for row in fact_orders.itertuples():
    # Generate noisy weights first
    noisy_weights = {}
    for cost_type_id, ratio in cost_type_ratios.items():
        noisy_weights[cost_type_id] = ratio * random.uniform(0.9, 1.1)

    # Normalize so weights sum to exactly 1
    total_weight = sum(noisy_weights.values())
    normalized_weights = {k: v / total_weight for k, v in noisy_weights.items()}

    # Now allocate cost using normalized weights - these will sum exactly to FulfillmentCost
    allocated_so_far = 0
    for i, cost_type_id in enumerate(cost_type_ids):
        if i == len(cost_type_ids) - 1:
            # Last cost type gets the remainder, avoiding rounding drift
            allocated_cost = round(row.FulfillmentCost - allocated_so_far, 2)
        else:
            allocated_cost = round(row.FulfillmentCost * normalized_weights[cost_type_id], 2)
            allocated_so_far += allocated_cost

        cost_rows.append({
            'OrderID': row.OrderID,
            'CostTypeID': cost_type_id,
            'Amount': allocated_cost
        })

fact_order_costs = pd.DataFrame(cost_rows)
fact_order_costs.to_csv(os.path.join(DATA_DIR, "Fact_Order_Costs.csv"), index=False)
print("Fact_Order_Costs created:", fact_order_costs.shape)
