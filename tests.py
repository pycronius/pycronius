from datetime import datetime
import unittest

from cronparser import CronParser
from rules import BasicCronRule


#TODO: test tz-aware datetime strings


class TestBasicCronRule(unittest.TestCase):

    def test_parse_field(self):
        r = BasicCronRule("* * * * * *")
        strs = {
            "5": {5},
            "2-9": set(xrange(2,10)),
            "20-30": set(xrange(20,31)), 
            "20-30/2": set(xrange(20,31,2)), 
            "*": set(xrange(0,60)),
            "*/3": set(xrange(0,60,3))
        }
        for f, v in strs.items():
            self.assertTrue(r.parse_field(f, 0, 59) == v)


    def test_parse(self):
        rule = BasicCronRule("* 7-19 * * 1-5 * ")

        self.assertTrue( all([m in rule.rulesets["minutes"] for m in xrange(0,60)]) )
        self.assertTrue( all([h in rule.rulesets["hours"] for h in xrange(7,20)]) )
        self.assertTrue( all([d in rule.rulesets["dom"] for d in xrange(1,32)]) )
        self.assertTrue( all([m in rule.rulesets["moy"] for m in xrange(1,13)]) )
        self.assertTrue( all([d in rule.rulesets["dow"] for d in xrange(1,6)]) )
        self.assertTrue( all([y in rule.rulesets["year"] for y in xrange(2000,2021)]) )


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


class TestBasicCronParser(unittest.TestCase):
    pass

    def test_holiday_rules(self):
        rules = [("open", "* 7-19 * * * *"), ("closed", "* 0-6 * * * *"), ("closed", "* 20-23 * * * *")]
        exceptions = [("closed", "* 0-8 * * 6-7 *"), ("closed", "* 17-23 * * 6-7 *"), ("closed", "* * 25 12 * *"), ("closed", "* * 4 7 * *")]

        for m in xrange(1,12):
            exceptions.append(("closed", "* * 1 %s * 2014" % m))

        cp = CronParser(rules, exceptions)

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
        cp = CronParser(
            [("open", "* 7-19 * * * *"), ("closed", "* 0-6 * * * *"), ("closed", "* 20-23 * * * *")],
            [("closed", "* 0-8 * * 6-7 *"), ("closed", "* 17-23 * * 6-7 *"), ("closed", "* * 25 12 * *"), ("closed", "* * 4 7 * *")]
        )


        # Weekday
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,12,0))[0], "open")
        
        # Weekday Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,19,21,30))[0], "closed")

        # Weekend
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,8,30))[0], "closed")
        
        # #Weekend Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,17,30))[0], "closed")
        
        # Christmas (Thursday)
        self.assertEqual(cp.pick_rules(datetime(2014,12,25,12,0))[0], "closed")







if __name__ == "__main__":
    # suite = unittest.TestSuite()
    # suite.addTest(TestBasicCronRule('test_parse'))
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicCronParser)
    suite = unittest.TestLoader().loadTestsFromNames(['tests.TestBasicCronRule', 'tests.TestBasicCronParser'])
    runner = unittest.TextTestRunner()
    runner.run(suite)
    