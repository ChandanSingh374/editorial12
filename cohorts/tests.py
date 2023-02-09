import json
import redis
import time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cohorts.models import *
from commons.cost_tracker import get_operation_cost, reset_operation_cost

redis_client = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)

class GetScoreBoardTests(APITestCase):
    fixtures = ['fixtures/initial.json', ]

    def setUp(self):
        super()
        redis_client.flushall()
        reset_operation_cost()

    def test_should_return_200(self):
        url = reverse('cohort_scoreboard', args=[1])
        response = self.make_new_request(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "API should return success response")

    def test_when_no_score_updated(self):
        url = reverse('cohort_scoreboard', args=[1])
        response = self.make_new_request(url)

        res_body = json.loads(response.content)
        self.assertEqual(len(res_body), 0, "Should return empty result")
        self.check_cost_expectation(100, 200, "Should hit DB to get detail")

    def test_non_empty_result_when_non_zero_score_exists_for_cohort_user(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response = self.make_new_request(url)

        res_body = json.loads(response.content)
        self.assertEqual(len(res_body), 1, "Should return non empty result")
        self.assertEqual(res_body[0].get("email"), 'Cohort1+user1@example.com', "Validate Returned Result")
        self.assertEqual(res_body[0].get("score"), 100, "Validate Returned Score")
        self.check_cost_expectation(100, 200, "Should hit DB to get detail")

    def test_second_request_for_same_cohort_fetched_from_cache(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(len(res_1_body), 1, "Should return non empty result")
        self.check_cost_expectation(100, 200, "1st fetch should hit DB to get detail")
        
        # Second Request
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertEqual(len(res_2_body), 1, "Should return non empty result")
        self.check_cost_expectation(1, 50, "2nd fetch should hit cache to get detail")

    def test_cohort_level_cache(self):
        # Update Cache For 1st cohort
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1_cohort_1 = self.make_new_request(url)
        
        # 1st Request cohort 1 Expectation
        res_1_cohort_1_body = json.loads(response_1_cohort_1.content)
        self.assertEqual(len(res_1_cohort_1_body), 1, "Should return non empty result for batch 1")
        self.check_cost_expectation(100, 200, "1st fetch for batch 1, should hit DB to get detail")

        # Update Cache For 2nd cohort
        url = reverse('cohort_scoreboard', args=[2])
        self.update_score(101, 2, 100)
        self.update_score(102, 2, 1000)
        self.update_score(103, 2, 10000)
        response_1_cohort_2 = self.make_new_request(url)
        
        # 1st Request cohort 2 Expectation
        res_1_cohort_2_body = json.loads(response_1_cohort_2.content)
        self.assertEqual(len(res_1_cohort_2_body), 3, "Should return non empty result for batch 2")
        self.check_cost_expectation(100, 200, "1st fetch for batch 2, should hit DB to get detail")
        
        # 2nd Request cohort 1
        url = reverse('cohort_scoreboard', args=[1])
        response_2_cohort_1 = self.make_new_request(url)

        # 2nd Request cohort 1 Expectation
        res_2_cohort_1_body = json.loads(response_2_cohort_1.content)
        self.assertEqual(len(res_2_cohort_1_body), 1, "Should return non empty result for batch 1")
        self.check_cost_expectation(1, 50, "2nd fetch for batch 1, should hit Cache to get detail")
        self.assertEqual(res_2_cohort_1_body, res_1_cohort_1_body, "Response from cache and DB should be same")

        # 2nd Request cohort 2
        url = reverse('cohort_scoreboard', args=[2])
        response_2_cohort_2 = self.make_new_request(url)

        # 2nd Request cohort 2 Expectation
        res_2_cohort_2_body = json.loads(response_2_cohort_2.content)
        self.assertEqual(len(res_2_cohort_2_body), 3, "Should return non empty result for batch 1")
        self.check_cost_expectation(1, 50, "2nd fetch for batch 2, should hit Cache to get detail")
        self.assertEqual(res_2_cohort_2_body, res_1_cohort_2_body, "Response from cache and DB should be same")

    def test_rebuild_cache_when_redis_data_flushed(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(len(res_1_body), 1, "Should return non empty result")
        self.check_cost_expectation(100, 200, "should hit DB to get detail")
        
        # Second Request
        redis_client.flushall()
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertEqual(len(res_2_body), 1, "Should return non empty result, even after redis flushed")
        self.check_cost_expectation(100, 200, "Should fetch detail from DB if Redis flushed and Rebuild Cache")

        # 3rd Request
        response_3 = self.make_new_request(url)

        # 3rd Request Expectation
        res_3_body = json.loads(response_3.content)
        self.assertEqual(len(res_3_body), 1, "Should return non empty result, after cache rebuild")
        self.check_cost_expectation(1, 50, "Should fetch detail from cache, after cache rebuild")

    def test_stale_data_capped_at_30_seconds(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(len(res_1_body), 1)
        self.check_cost_expectation(100, 200, "should hit DB to get detail")
        
        # Second Request
        self.update_score(2, 1, 100)
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertGreaterEqual(len(res_2_body), 1, "Allowed to show stale data for immediate request")
        self.check_cost_expectation(1, 50, "Should fetch detail from cache")

        # 3rd Request after 30sec
        # time.sleep(30)
        response_3 = self.make_new_request(url)

        # 3rd Request Expectation
        res_3_body = json.loads(response_3.content)
        self.assertEqual(len(res_3_body), 2, "Should return updated scoreboard")

    def update_score(self, user_id, cohort_id, score):
        bu = CohortUser.objects.filter(cohort_id=cohort_id, user_id=user_id).first()
        bu.score = score
        bu.save()

    def check_cost_expectation(self, cost_min, cost_max, message=None):
        self.assertLessEqual(get_operation_cost(), cost_max, message)
        self.assertGreaterEqual(get_operation_cost(), cost_min, message)

    def make_new_request(self, url):
        reset_operation_cost()
        return self.client.get(url, format='json')
