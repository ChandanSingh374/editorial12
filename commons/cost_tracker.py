TOTAL_OPERATION_COST = 0
COST_FOR = {
    "db": 100,
    "redis": 1
}

def track_redis_hit():
    update_operation_cost_for("redis")

def track_db_hit():
    update_operation_cost_for("db")

def update_operation_cost_for(update_for):
    global TOTAL_OPERATION_COST
    TOTAL_OPERATION_COST += COST_FOR.get(update_for, 0)

def get_operation_cost():
    global TOTAL_OPERATION_COST
    return TOTAL_OPERATION_COST

def reset_operation_cost():
    global TOTAL_OPERATION_COST
    TOTAL_OPERATION_COST = 0
