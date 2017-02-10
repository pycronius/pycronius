# pycronius

Pycronius is a fully-tested, benchmarked utility for efficiently matching datetime objects and cron rules.  

For example, a business might have various sets of opening and closing hours (e.g. weekday and weekend),
and sets of exceptions to this rule (e.g. holidays).  

With pycronius we could answer questions such as whether or not the business is open right now, 
tomorrow at 9am, Christmas at 4pm, etc.

Another perfectly reasonable example is the more traditional crontab, although this was not the original motivation.

## Why cron strings?

Because they are compact, simple, visually verifiable, and in wide use.


## Alright, cool, now show me some code

```python
from pycronius import Scheduler

#Open 7am to 8pm
rules = [("open", "* 7-19 * * * *"), ("closed", "* 0-6 * * * *"), ("closed", "* 20-23 * * * *")]

#Open 9am to 5pm on weekdays, and closed Christmas and July 4th
exceptions = [("closed", "* 0-8 * * 6-7 *"), ("closed", "* 17-23 * * 6-7 *"), ("closed", "* * 25 12 * *"), ("closed", "* * 4 7 * *")]

scheduler = Scheduler(rules, exceptions, 2010, 2020)

print scheduler.get_matching_rules(datetime(2014, 12, 19, 12, 0)) # -> ["open"]
```

## CronRange strings

One drawback of standard cron strings is that they are inconvenient for representing periods that do not begin or end exactly on the hour. With standard cron strings this requires defining multiple rules to handle non-contiguous blocks of time. For example, say our hypothetical business opens at 7:30 and closes at 19:00.  We would need the following strings:
* `("closed", "* 0-6 * * * *")`
* `("closed", "0-30 7 * * * *")`
* `("open", "30-59 7 * * * *")`
* `("open", "* 8-18 * * * *")`
* `("closed", "* 19-23 * * * *")`

Since one of the motivating use cases was managing opening hours, pycronius supports strings where 
the first two fields are the start and stop time in HH:MM format, and the last four are in the traditional style.
Now the example above can be represented like this:
* `("closed", "0:00 7:29 * * * *")`
* `("open", "7:30 19:00 * * * *")`
* `("closed", "19:01 23:59 * * * *")`

Using these strings requires no additional configuration, and they can be mixed with traditional strings at will.


## Scheduler Documentation

### Initialization

The `Scheduler` class takes four parameters:

##### `rules`
A list of tuples that look like (id (a hashable object), cron string) e.g. (1, "* * * * * *"), where the fields are either 
"minute hour day-of-month month day-of-week year" or "start-time stop-time day-of-month month day-of-week year".

For traditional cron string, each field is separated by a space, and can consist of either:
* digit (e.g. `"12"`)
* asterisk (wildcard, e.g. `"*"`)

Additionally these can be separated by the following in the standard way:
* `"-"` (range, inclusive on both end-points, e.g. `"2000-2020"`)
* `"/"` (interval repetition, e.g. "*/6", or `"1-30/2"`)
* `","` (concatenate field defintions, e.g. `"*/3,*/2"`)

Rules can overlap, which simply means that multiple rules match for a single datetime.
It is up to the user to define the appropriate cron rules for their application.

##### `exceptions`
The `exceptions` argument has the same type and syntax as the `rules` argument, however the semantics are different.
These are meant to be exceptions to the rules defined in `rules`, e.g. the business is closed on Christmas.
If such an exception is defined, then even if the business would normally be open, 
`Scheduler.get_matching_rules()` will return closed for any datetime on December 25th.

If there are multiple exceptions defined for the same time, `Scheduler.get_matching_rules()` will return the first
one it encounters, which is not defined.  Unfortunately, the current version of pycronius does not check for overlapping
exceptions, but since this will almost certainly lead to unpredictable behavior, for now, the user is strongly urged 
not to define such exceptions.

##### `start_year` and `stop_year`
These are YYYY format integers, and are used bound the year field for wildcard and wildcard intervals.  
Every other field has these boundaries pre-defined (e.g. 24 hours per day), however in general, years have 
no such boundary, so it is best to define this on a per-application basis.  


### Usage

After initializing a Scheduler instance, you can get the matching rules for a datetime object with
`Scheduler.get_matching_rules(datetime_object)`.  This will return a list of ids as defined in `rules` and 
`exceptions`.  This is a list because it is possible that more than one rule matches a given datetime object


### Other considerations

* `exceptions` that are defined as all minutes/hours of a certain date (e.g. "* * 4 7 * 2015") are handled in a
special, optimized way.
*  Even with the HH:MM style strings, there are some rule types which pycronius is still pretty bad at modeling, 
    e.g. third friday of every month.  Luckily it is not so hard to add subclasses of `rules.BasicCronRule` to
    handle extra use cases.
