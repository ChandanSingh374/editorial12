from batches.models import BatchUser
from commons.redis import performRedisOps
from commons.cost_tracker import track_db_hit

def fetchRankListFromDB(batch_id):
    track_db_hit()

    return BatchUser.objects.filter(
        score__gt=0,
        batch_id=batch_id
    ).order_by('-score').values_list('user__email', 'score')

def FetchRankList(batch_id):
    SCORE_BOARD_KEY = f'batch_rank_list:{batch_id}.'
    if performRedisOps("exists", SCORE_BOARD_KEY):
        return performRedisOps("zrevrange", SCORE_BOARD_KEY, "0", "-1", "WITHSCORES")
    else:
        batch_users = fetchRankListFromDB(batch_id)
        score_list = {batch_user[0]: batch_user[1] for batch_user in batch_users}
        if score_list:
            performRedisOps("zadd", SCORE_BOARD_KEY, score_list)
            performRedisOps('expire', SCORE_BOARD_KEY, 2)
        return batch_users

def updateScoreSave(user_id, batch_id, new_score):
    # This methods is always called when batch user is updated in DB.
    pass

