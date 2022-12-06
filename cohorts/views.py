from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cohorts.models import CohortUser
from cohorts.scoreboard import FetchRankList
from cohorts.serializer import ScoreboardSerializer

class CohortScoreBoard(APIView):
    def get(self, request, cohort_id, format=None):
        """
        Return a list of all users with score in ranklist with score > 0.
        """
        rank_list = FetchRankList(cohort_id)
        results = ScoreboardSerializer(rank_list, many=True).data
        return Response(data=results, status=status.HTTP_200_OK)

    def post(self, request, cohort_id, format=None):
        """
        API to update score for batch user
        """
        user_id = int(request.POST.get('user_id'))
        score = int(request.POST.get('score'))
        cohort_user = CohortUser.objects.filter(user_id=user_id, cohort_id=cohort_id).first()
        if cohort_user is not None:
            cohort_user.score = score
            cohort_user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
