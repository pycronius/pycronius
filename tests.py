from datetime import datetime
import unittest

from scheduler import Scheduler
from rules import *


#TODO: test tz-aware datetime strings


class TestBasicCronRule(unittest.TestCase):

    def test_parse_field(self):
        strs = {
            "5": [5],
            "2-9": xrange(2,10),
            "20-30": xrange(20,31), 
            "20-30/2": xrange(20,31,2), 
            "*": xrange(0,60),
            "*/3": xrange(0,60,3),
            "1,2-10/2,13-15": [1,2,4,6,8,10,13,14,15]
        }
        for f, v in strs.items():
            rule = BasicCronRule.parse_field(f, 0, 59)
            self.assertTrue(all([x in rule for x in v]))

        with self.assertRaises(InvalidFieldError):
             BasicCronRule.parse_field("1-*", 0, 0)


    def test_parse(self):
        rule = BasicCronRule("* 7-19 * * 1-5 */2", start_year=1999, stop_year=2021)

        self.assertTrue( all([m in rule.rulesets["minutes"] for m in xrange(0,60)]) )
        self.assertTrue( all([h in rule.rulesets["hours"] for h in xrange(7,20)]) )
        self.assertTrue( all([d in rule.rulesets["dom"] for d in xrange(1,32)]) )
        self.assertTrue( all([m in rule.rulesets["moy"] for m in xrange(1,13)]) )
        self.assertTrue( all([d in rule.rulesets["dow"] for d in xrange(1,6)]) )
        self.assertTrue( all([y in rule.rulesets["year"] for y in xrange(1999,2021,2)]) )
        self.assertFalse( all([y in rule.rulesets["year"] for y in xrange(1999,2021)]) )
        self.assertFalse( all([y in rule.rulesets["year"] for y in xrange(1999,2024,2)]) )

        with self.assertRaises(InvalidCronStringError):
             BasicCronRule.parse("1-* * * * * *")
    


    def test_is_holiday(self):
        rule = BasicCronRule("* 7-19 * * 1-5 * ")

        self.assertFalse(rule.is_holiday("* * * * * *"))
        self.assertFalse(rule.is_holiday("* * 12 25 * *"))
        self.assertTrue(rule.is_holiday("* * 4 7 * 2015"))
        self.assertFalse(rule.is_holiday("* * 4-6 7 * 2015"))
        self.assertFalse(rule.is_holiday("*/2 * 4 7 * 2015"))

        self.assertEqual(rule.holiday_tuple("* * 4 7 * 2015"), (4,7,2015))


    def test_contains(self):
        # Weekday
        rule = BasicCronRule("* 7-19 * * * *")
        self.assertTrue(rule.contains(datetime(2014,12,19,12,0)))
        
        # Weekday Night
        rule = BasicCronRule("* 20-23 * * * *")
        self.assertTrue(rule.contains(datetime(2014,12,19,21,30)))

        # Weekend
        rule = BasicCronRule("* 0-8 * * 6-7 *")
        self.assertTrue(rule.contains(datetime(2014,12,20,8,30)))
        
        #Weekend Night
        rule = BasicCronRule("* 17-23 * * 6-7 *")
        self.assertTrue(rule.contains(datetime(2014,12,20,17,30)))
        
        # Christmas (Thursday)
        rule = BasicCronRule("* * 25 12 * *")
        self.assertTrue(rule.contains(datetime(2014,12,25,12,0)))



class TestCronRangeRule(unittest.TestCase):

    def test_parse_field(self):
        strs = {
            "5": [5],
            "2-9": xrange(2,10),
            "20-30": xrange(20,31), 
            "20-30/2": xrange(20,31,2), 
            "*": xrange(0,60),
            "*/3": xrange(0,60,3)
        }

        for f, v in strs.items():
            rule = BasicCronRule.parse_field(f, 0, 59)
            self.assertTrue(all([x in rule for x in v]))
        
        hhmm = CronRangeRule.parse_field("13:45")
        
        self.assertEqual(hhmm.hour, 13)
        self.assertEqual(hhmm.minute, 45)


    def test_parse(self):
        rule = CronRangeRule("7:30 19:15 * * 1-5 * ")

        self.assertTrue( rule.rulesets["start"].hour == 7 and rule.rulesets["start"].minute == 30 )
        self.assertTrue( rule.rulesets["stop"].hour == 19 and rule.rulesets["stop"].minute == 15 )
        self.assertTrue( all([d in rule.rulesets["dom"] for d in xrange(1,32)]) )
        self.assertTrue( all([m in rule.rulesets["moy"] for m in xrange(1,13)]) )
        self.assertTrue( all([d in rule.rulesets["dow"] for d in xrange(1,6)]) )
        self.assertTrue( all([y in rule.rulesets["year"] for y in xrange(2000,2021)]) )

        with self.assertRaises(InvalidCronStringError):
            CronRangeRule.parse("1:23 12:34 */ * * *")

        with self.assertRaises(InvalidCronStringError):
            CronRangeRule.parse("* * * * * *")


    def test_contains(self):
        # Weekday
        rule = CronRangeRule("7:30 19:15 * * * *")
        self.assertTrue(rule.contains(datetime(2014,12,19,12,0)))
        self.assertTrue(rule.contains(datetime(2014,12,19,7,30)))
        self.assertFalse(rule.contains(datetime(2014,12,19,19,20)))
        
        # Weekday Night
        rule = CronRangeRule("20:00 23:59 * * * *")
        self.assertTrue(rule.contains(datetime(2014,12,19,21,30)))
        self.assertFalse(rule.contains(datetime(2014,12,19,19,59)))

        # Weekend
        rule = CronRangeRule("00:00 08:00 * * 6-7 *")
        self.assertTrue(rule.contains(datetime(2014,12,20,8,0)))
        self.assertFalse(rule.contains(datetime(2014,12,20,8,1)))
        self.assertFalse(rule.contains(datetime(2014,12,17,7,0)))


    def test_looks_like_range_rule(self):
        self.assertTrue(CronRangeRule.looks_like_range_rule("7:30 19:00 * * * *"))
        self.assertFalse(CronRangeRule.looks_like_range_rule("* * * * * *"))
        self.assertFalse(CronRangeRule.looks_like_range_rule("* 19:00 * * * *"))
        self.assertFalse(CronRangeRule.looks_like_range_rule("7:30 * * * * *"))


    def test_is_valid(self):
        self.assertTrue(CronRangeRule.is_valid("7:30 19:00 * * * *"))
        self.assertFalse(CronRangeRule.is_valid("7:30 19:00 * */ * *"))
        self.assertFalse(CronRangeRule.is_valid("* * * * * *"))
        self.assertFalse(CronRangeRule.is_valid("* 19:00 * * * *"))
        self.assertFalse(CronRangeRule.is_valid("7:30 * * * * *"))
                

class TestScheduler(unittest.TestCase):

    def test_holiday_rules(self):
        rules = [("open", "* 7-19 * * * *"), ("closed", "* 0-6 * * * *"), ("closed", "* 20-23 * * * *")]
        exceptions = [("closed", "* 0-8 * * 6-7 *"), ("closed", "* 17-23 * * 6-7 *"), ("closed", "* * 25 12 * *"), ("closed", "* * 4 7 * *")]

        for m in xrange(1,12):
            exceptions.append(("closed", "* * 1 %s * 2014" % m))

        cp = Scheduler(rules, exceptions)

        # Weekday
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,12,0))[0], "open")
        
        # Weekday Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,21,30))[0], "closed")

        # Weekend
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,8,30))[0], "closed")
        
        #Weekend Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,17,30))[0], "closed")
        
        # First of April (Tuesday)
        self.assertEqual(cp.pick_rules(datetime(2014,4,1,12,0))[0], "closed")



    def test_pick_rules(self):
        cp = Scheduler(
            [("open", "7:00 19:30 * * * *"), ("closed", "* 6 * * * *"), ("closed", "19:31 23:59 * * * *")],
            [("closed", "0:00 8:30 * * 6-7 *"), ("closed", "18:30 23:59 * * 6-7 *"), ("closed", "* * 24,25 12 * *"), ("closed", "* * 4 7 * *"), ("closed", "* * 5 4 * 2015")]
        )


        # Weekday
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,18,31))[0], "open")
        
        # Weekday Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,19,31))[0], "closed")

        # Weekend Morning
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,8,0))[0], "closed")

        # Weekend Day
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,12,0))[0], "open")
        
        # #Weekend Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,18,31))[0], "closed")
        
        # Christmas (Thursday)
        self.assertEqual(cp.pick_rules(datetime(2014,12,25,12,0))[0], "closed")

        # Christmas Eve (Wednesday)
        self.assertEqual(cp.pick_rules(datetime(2014,12,24,12,0))[0], "closed")

        # Easter (Sunday)
        self.assertEqual(cp.pick_rules(datetime(2015,4,5,12,0))[0], "closed")


    def test_start_stop(self):
        cp = Scheduler(
            [("odd_year", "* * * * * *")],
            [("even_year", "* * * * * */2")],
            start_year=1990, stop_year=1999
        )

        self.assertEqual(cp.pick_rules(datetime(1991,12,19,18,31))[0], "odd_year")
        self.assertEqual(cp.pick_rules(datetime(1992,12,19,18,31))[0], "even_year")
        self.assertEqual(cp.pick_rules(datetime(2000,12,19,18,31)), [])



if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TestBasicCronRule('test_parse_field'))
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicScheduler)
    suite = unittest.TestLoader().loadTestsFromNames(['tests'])
    runner = unittest.TextTestRunner()
    runner.run(suite)
    