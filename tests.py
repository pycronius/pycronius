from datetime import datetime
import unittest

from cronparser import CronParser



class TestBasicCronParser(unittest.TestCase):

    def test_parse_field(self):
        cp = CronParser()
        strs = {
            "5": {5},
            "2-9": set(xrange(2,10)),
            "20-30": set(xrange(20,31)), 
            "20-30/2": set(xrange(20,31,2)), 
            "*": set(xrange(0,60)),
            "*/3": set(xrange(0,60,3))
        }
        for f, v in strs.items():
            self.assertTrue(cp.parse_field(f, 0, 59), cp.parse_field(f, 0, 59) == v)


    def test_parse(self):
        cp = CronParser()
        ruleset = cp.parse("* 7-19 * * 1-5 * ")

        self.assertTrue(ruleset["minutes"] == set(xrange(0,60)))
        self.assertTrue(ruleset["hours"] == set(xrange(7,20)))
        self.assertTrue(ruleset["dom"] == set(xrange(1,32)))
        self.assertTrue(ruleset["moy"] == set(xrange(1,13)))
        self.assertTrue(ruleset["dow"] == set(xrange(1,6)))
        self.assertTrue(ruleset["year"] == set(xrange(2000,2026)))


    def test_is_holiday(self):
        cp = CronParser()
        self.assertFalse(cp.is_holiday("* * * * * *"))
        self.assertFalse(cp.is_holiday("* * 12 25 * *"))
        self.assertTrue(cp.is_holiday("* * 4 7 * 2015"))
        self.assertFalse(cp.is_holiday("* * 4-6 7 * 2015"))
        self.assertFalse(cp.is_holiday("*/2 * 4 7 * 2015"))

        self.assertEqual(cp.holiday_tuple("* * 4 7 * 2015"), (4,7,2015))


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
        
        #Weekend Night
        self.assertEqual(cp.pick_rules(datetime(2014,12,20,17,30))[0], "closed")
        
        # Christmas (Thursday)
        self.assertEqual(cp.pick_rules(datetime(2014,12,25,12,0))[0], "closed")







if __name__ == "__main__":
    # suite = unittest.TestSuite()
    # suite.addTest(TestBasicCronParser('test_pick_rules'))
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicCronParser)
    runner = unittest.TextTestRunner()
    runner.run(suite)
    