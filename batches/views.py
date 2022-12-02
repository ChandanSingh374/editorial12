from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from batches.models import BatchUser
from batches.scoreboard import FetchRankList
from batches.serializer import ScoreboardSerializer

class BatchScoreBoard(APIView):
    def get(self, request, batch_id, format=None):
        """
        Return a list of all users with score in ranklist with score > 0.
        """
        rank_list = FetchRankList(batch_id)
        results = ScoreboardSerializer(rank_list, many=True).data
        return Response(data=results, status=status.HTTP_200_OK)

    def post(self, request, batch_id, format=None):
        """
        API to update score for batch user
        """
        user_id = int(request.POST.get('user_id'))
        score = int(request.POST.get('score'))
        BatchUser.objects.filter(user_id=user_id, batch_id=batch_id).update(score=score)
        return Response(status=status.HTTP_204_NO_CONTENT)
