from cohorts.models import CohortUser
from commons.redis import performRedisOps
from commons.cost_tracker import track_db_hit

def fetchRankListFromDB(cohort_id):
    track_db_hit()
    return CohortUser.objects.filter(
        score__gt=0,
        cohort_id=cohort_id
    ).order_by('-score').values_list('user__email', 'score')

def FetchRankList(cohort_id):
    SCORE_BOARD_KEY = f'batch_rank_list:{cohort_id}.'
    if performRedisOps("exists", SCORE_BOARD_KEY):
        return performRedisOps("zrevrange", SCORE_BOARD_KEY, "0", "-1", "WITHSCORES")
    else:
        cohort_users = fetchRankListFromDB(cohort_id)
        score_list = {cohort_user[0]: cohort_user[1] for cohort_user in cohort_users}
        if score_list:
            performRedisOps("zadd", SCORE_BOARD_KEY, score_list)
            performRedisOps('expire', SCORE_BOARD_KEY, 30)
        return cohort_users

def updateUserRank(user_email, cohort_id, new_score):
    SCORE_BOARD_KEY = f'batch_rank_list:{cohort_id}.'
    if performRedisOps("exists", SCORE_BOARD_KEY):
        performRedisOps("zadd", SCORE_BOARD_KEY, {user_email: new_score})
