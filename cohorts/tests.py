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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_result_if_score_not_updated(self):
        url = reverse('cohort_scoreboard', args=[1])
        response = self.make_new_request(url)

        res_body = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(res_body), 0)

    def test_should_return_data_if_score_updated(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response = self.make_new_request(url)

        res_body = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(res_body), 1)
        self.assertEqual(res_body[0].get("email"), 'Cohort1+user1@example.com')
        self.assertEqual(res_body[0].get("score"), 100)
        self.check_cost_expectation(100, 200)

    def test_for_second_request_for_same_cohort_should_fetch_from_cache(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(len(res_1_body), 1)
        self.check_cost_expectation(100, 200)
        
        # Second Request
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(len(res_2_body), 1)
        self.check_cost_expectation(1, 50)

    def test_should_set_cohort_level_cache(self):
        # Update Cache For 1st cohort
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1_cohort_1 = self.make_new_request(url)
        
        # 1st Request cohort 1 Expectation
        res_1_cohort_1_body = json.loads(response_1_cohort_1.content)
        self.assertEqual(response_1_cohort_1.status_code, 200)
        self.assertEqual(len(res_1_cohort_1_body), 1)
        self.check_cost_expectation(100, 200)

        # Update Cache For 2nd cohort
        url = reverse('cohort_scoreboard', args=[2])
        self.update_score(101, 2, 100)
        self.update_score(102, 2, 1000)
        self.update_score(103, 2, 10000)
        response_1_cohort_2 = self.make_new_request(url)
        
        # 1st Request cohort 2 Expectation
        res_1_cohort_2_body = json.loads(response_1_cohort_2.content)
        self.assertEqual(len(res_1_cohort_2_body), 3)
        self.check_cost_expectation(100, 200)
        
        # 2nd Request cohort 1
        url = reverse('cohort_scoreboard', args=[1])
        response_2_cohort_1 = self.make_new_request(url)

        # 2nd Request cohort 1 Expectation
        res_2_cohort_1_body = json.loads(response_2_cohort_1.content)
        self.assertEqual(len(res_2_cohort_1_body), 1)
        self.check_cost_expectation(1, 50)
        self.assertEqual(res_2_cohort_1_body, res_1_cohort_1_body)

        # 2nd Request cohort 2
        url = reverse('cohort_scoreboard', args=[2])
        response_2_cohort_2 = self.make_new_request(url)

        # 2nd Request cohort 2 Expectation
        res_2_cohort_2_body = json.loads(response_2_cohort_2.content)
        self.assertEqual(len(res_2_cohort_2_body), 3)
        self.check_cost_expectation(1, 50)
        self.assertEqual(res_2_cohort_2_body, res_1_cohort_2_body)

    def test_if_redis_data_flushed_should_rebuild_cache(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(len(res_1_body), 1)
        self.check_cost_expectation(100, 200)
        
        # Second Request
        redis_client.flushall()
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(len(res_2_body), 1)
        self.check_cost_expectation(100, 200)

    def test_only_allow_30_sec_of_stale_data(self):
        url = reverse('cohort_scoreboard', args=[1])
        self.update_score(1, 1, 100)
        response_1 = self.make_new_request(url)
        
        # 1st Request Expectation
        res_1_body = json.loads(response_1.content)
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(len(res_1_body), 1)
        self.check_cost_expectation(100, 200)
        
        # Second Request
        self.update_score(2, 1, 100)
        response_2 = self.make_new_request(url)

        # 2nd Request Expectation
        res_2_body = json.loads(response_2.content)
        self.assertGreaterEqual(len(res_2_body), 1)

        # 3rd Request after 30sec
        time.sleep(30)
        response_3 = self.make_new_request(url)

        # 3rd Request Expectation
        res_3_body = json.loads(response_3.content)
        self.assertEqual(len(res_3_body), 2)

    def update_score(self, user_id, cohort_id, score):
        bu = CohortUser.objects.filter(cohort_id=cohort_id, user_id=user_id).first()
        bu.score = score
        bu.save()

    def check_cost_expectation(self, cost_min, cost_max):
        self.assertLessEqual(get_operation_cost(), cost_max)
        self.assertGreaterEqual(get_operation_cost(), cost_min)

    def make_new_request(self, url):
        reset_operation_cost()
        return self.client.get(url, format='json')
