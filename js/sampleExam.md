# BEGIN GROUP Preliminaries
You can complete and submit these questions before the exam starts.

# BEGIN QUESTION
What is your *true* name? with sprinkles
# INPUT SHORT_ANSWER
# END QUESTION

# BEGIN QUESTION
What is your student ID number?
SeriouslY?
# INPUT SHORT_ANSWER
# END QUESTION

# END GROUP

# BEGIN GROUP WWPD [6]
*This is some very important text*. This text is not so important.

# BEGIN QUESTION [2]
What is cat?

# INPUT OPTION fat
# INPUT OPTION smart
# INPUT OPTION cute

# END QUESTION

# BEGIN QUESTION [4]
What _really_ is cat?

# INPUT SHORT_ANSWER

# END QUESTION

# END GROUP

# BEGIN GROUP WWPD? [6]

# BEGIN QUESTION [3]

Solve the following integral:
$$
    \int_{0}^\infty e^{-x^2 / 2} \, \mathrm{d}x
$$

# INPUT OPTION fat
# INPUT OPTION $\sqrt{2\pi}$
# INPUT OPTION cute

# END QUESTION

# BEGIN QUESTION [7]
What would the following Python code do?
```
from operator import sub

z = (lambda x: lambda y: 2 * (y-x))(3)

def breath(f, count=1):
    if count > 1:
        print(count)
    count += 1
    return lambda x, y: f(x+1, y)

class Day:
    aqi = 10
    def __init__(self, aqi=0):
        if aqi > self.aqi:
            self.aqi = aqi
         self.n = []

def mask(self, limit):
    def f(aqi):
        if aqi > limit:
            self.n.append(aqi-limit)
        return self.mask(aqi)
    return f

class Week(Day):
    aqi = 50

m, t = Day(), Week(199)
t.mask(200)(100)(150)(160)
Day.aqi = 140
t.aqi = 160
```

# INPUT SHORT_ANSWER

# END QUESTION

# END GROUP
