# nKode analysis

Luke Oeding (Auburn University)

## What is an nKode?
An nKode consists of a passcode $P$ selected utilizing the following setup:

* a $k$ digit keypad, where each key has:
* $p$ properties (position, central number, color, letter, emoji,...)
* $m$ options for each property (\# positions, \# central numbers, \# colors, \# letters, \# emoji, ... )

    - In principle the number of options for each property doesn't have to be the same, but for the sake of our analysis, we make this uniform choice.
    - Typically one wants to have all letters displayed exactly once on the keypad for any instance of a keypad, so we take $m = k$.

* $\ell$ = length of the passcode, which is a sequence of $\ell$ letters (options) selected from any of the options. 
* a shuffling rule (the split-shuffle)

## Split shuffling

For each attempt at entering a passcode (except for the initial login challenge) the keypad is shuffled by a split-shuffle, which shuffles $s =\lfloor \frac{p}{2}\rfloor$ of the properties on the keys. The reason for this is that if nothing is shuffled $(s=0)$, then one observation of a passcode entry would be sufficient to learn the passcode, and if $s = p$, then just 2 observations might be sufficient for learning the passcode (as long as everything is actually permuted). The $s=p$ case is used by the organization to learn the intended nKode from the user by asking them to type it 2 times. 

## Math questions

We would like a function $E = E(k,p,m,\ell)$ of the entropy of the passcode / nKode.

We would like a function  $N = N(k,p,m,\ell,s)$ of views of correctly entered nKodes that an intruder would need to learn a passcode from observations.  

## Entropy 

We should actually think of different types of entropy for nKodes. 

- First we consider the entropy of the passcode itself. 
- Second, we consider the entropy of the keypad sequence. 
- Third, we consider the entropy of a sequence of successful nKode logins.

### Passcode Entropy

The total number of available passcodes with
$\ell$ letters selected from an alphabet with $N = mp$ symbols, with replacement is

$$ (mp)^\ell $$

So the entropy of the set of passcodes is 

$$ E(m,p,\ell) = \log_2[(mp)^\ell] = \ell \frac{\log(mp)}{\log(2)}$$

So, for example, when $m=10$ and $p = 7$, the alphabet has 70 letters, and a passcode of length $\ell = 4$ would have entropy:

$$ E(10,7,4) =  4\log(70)/\log(2) = 24.5\; \text{bits}$$

$$ E(10,7,6) =  6\log(70)/\log(2) = 36.8\; \text{bits}$$

Relevant is the entropy per symbol, which is $ E(m,p,1)  = \log_2(m) +\log_2(p) = \frac{\log(m) + \log(p)}{\log(2)}$.

For instance:
$ E(10,7,1) =  \log(70)/\log(2) = 6.13\; \text{bits}$

### nKode Entropy

If one is interested in the likelihood of a single attempt randomly entered nKode being successful, there is a drastic reduction in entropy because $m=k$ and $p$ is ignored. 

The total number of available passcodes with
$\ell$ letters selected from an alphabet with $k$ keys, with replacement is

$$ k^\ell $$

So the entropy of the one time keypad is 

$$ E(k,\ell) = \log_2[(k)^\ell] = \ell \frac{\log(k)}{\log(2)}$$

So, for example, when $k=10$ a passcode of length $\ell = 4$ would have entropy:
$ E(10,4) =  4\log(10)/\log(2) = 13.28\; \text{bits}$

The entropy per symbol, which is $ E(k,1)  = \log_2(k) = \frac{\log(k)}{\log(2)}$.

In the case $k=10$ we have $E(10,1) = 3.22 \; \text{bits}$. 

## Eavesdropper analysis

We are interested in understanding the number of times an eavesdropping intruder would have to observe the user entering their nKode before the intruder would successfully obtain the passcode. 

### Eavesdropper with split shuffles

[Brooks Brown says that the lower bound is $\min\{3,  s \log_2+1\}$, where $s$ is the number of attribute sets, for an nKode of complexity $c=1$, regardless of nKode length $l$, or the number of tiles $t$.]


Regarding the eavesdropper attack we should also consider the case of a keystroke recorder that doesn't observe the labels on the keys of the nKode keypad. 
Blind single attacks and repeated blind attempts that successfully log in, and learning the nKode. 

[Still working on this part. I want to ensure I understand the split shuffle correctly first - still reading and studying this.]

## Blind keystroke recording analysis

### Single blind attempt

The probability that a (blind) randomly entered key-string will yield a successful login:

$
R = \frac{\text{Num}(\text{passcodes that would yield a correct login})}{\text{Num}(\text{possible passcodes})}.
$

(Num stands for 'number of'.)
This should be simply computed using the number of keys $k$ and the length $l$ of the passcode:

$
R = (1/k)^l.
$

For example, a 6 digit pin would yield a one-in-a-million chance of blindly hitting the correct passcode. 

### Frequency analysis attack

For the moment we only consider the case of $p=2$, which could be the case if the nKode keypad only has $2$ properties (place and central number). This situation might also be achieved if the user decides to only use 2 of the properties to generate their nKode.

Note that if a user insists on only using the placement value of the keys in an nKode to select their password, then they effectively have reduced the complexity or entropy of their password to that of the normal keypad, and an adversary could use frequency analysis to increase the likelihood of guessing a correct password. However, if the user were to use only the number values on the keypad, they would still only have the entropy of a standard keypad generated password, however, because of the shuffling of the letters, using an nKode provides the user with some protection against frequency analysis attacks in the case of a blind intruder.

For example, it is know that users pick passwords like 1234 or 123456 much more frequently than of any other password. If the intruder is able to observe the user typing one of these passcodes on an nKode keypad, then they would be able to guess the passcode with higher probability than random. However, if the intruder is only able to record keystrokes, but not see the display of the nKode keypad, then the intruder would only guess the correct passcode at the frequency of guessing a permutation of the correct passcode. In the case of $\ell $ consecutive digits, the keystroke intruder would only observe $\ell$ distinct keys being typed. The number of such passcodes is $\binom{k}{\ell}$. So in the case of a $k=10$ digit keypad, the number of $\ell=4$ digit passcodes with distinct entries is $\binom{10}{4} = 210$, and when $\ell = 6$ we also have $\binom{10}{6} = 210$. So, after one observation indicating that the passcode consists of $\ell$ distinct digits, the intruder would have probability $P = 1/\binom{k}{\ell}$ of guessing the passcode. 
It is known that the expected number of trials until the first success would be $1/P$.  In this case it would take the intruder on average $\binom{k}{\ell}$ attempts to successfully log in (without guessing the passcode). Even in the case of the 4 digit PIN where the intruder guesses that the passcode consists of the first $4$ digits, (or consecutive or even just distinct) integers the nKode obtains an increase in security for the user by a factor of approximately 210 since the key recording intruder would guess the password 1234 on the first attempt on a standard keypad, but would need approximately 210 trials to successfully log in. 

### Multiple blind attempts for a large userbase (Password spraying)

However, if the adversary were to attempt to hack a large number of users, some of their accounts would be compromised for at least one login. For this discussion we assume the intruder has access to $U$ names in the username database. If the blind probability of guessing is $R$, the probability that for a group of $U$ users no one is hacked is $(1-R)^U$.

In the case of 4 digit passcodes, and one million users, $U=10^6$, the probability of not hacking anyone is $(1-R)^U = (1-1/(10)^4)^{10^6} = 3.7*10^{-44}\%$, so the probability of hacking at least one user one time is essentially $100\%$. The probability of hacking $h$ users is $\binom{R}{h}(R)^h(1-R)^{U-h}$, and the probability of hacking up to $H$ users is $\sum_{h=0}^H\binom{R}{h}(R)^h(1-R)^{U-h}$. At some point these formulas take a while to compute and one replaces the sums with the integral $(U-H)\binom{U}{H}\int_0^{1-R} t^{U-H-1}(1-t)^H dt$.

In the case of 6 digit passcodes, and one million users, $U=10^6$, the probability of not hacking anyone is $(1-R)^U = (1-\frac{1}{10^6})^{10^6} = 37\%$, so the probability of hacking at least one user one time is $63\%$. 
The probability of 0 or 1 people is $(1-R)^U + \binom{U}{1}R^{1}(1-R)^{U-1} = (1-\frac{1}{10^6})^{10^6} + \binom{10^6}{1}\left(\frac{1}{10^6}\right)^1(1-\frac{1}{10^6})^{10^6-1}= 73.6\%$, so the probability of hacking at least two users is $26.4\%$. 

The point here is that 10-digit keypads and nKode keypads have the same susceptibility to blind guessing for one time access (if one ignores the use of frequently used PINs). It is known that password spraying can be an even more powerful attack when the intruder chooses the most commonly used passwords first. 

### Username database guessing

For another example, consider the following typical University's user database policy. Users are assigned a username of the form $abcN$, with $a,b,c$ any letters representing their initials ($z$ used for missing middle names) and $N$ a 4-digit number, starting from $0000$ and incrementing every time the initial is repeated. The set of initials is not uniformly distributed (names staring with U or X are rare, whereas names starting with $S$ are quite common), and the fact that the number $N$ is incremented, instead of random, means that a hacker can successfully guess a significant percentage of the username database. In the less realistic or less memorable situation of uniform choices of $abc$ and $0\leq N\leq 300$, an intruder could make a database of $26^3\cdot 300 = 5.3\text{M}$ potential users. In the case of a large university with an alumni base of $500\text{k}$, approximately 1 in 10 of the guessed user names would be actual usernames. This ratio improves significantly (though we didn't do the computation) if one only attempts to find the most common initials. 

The upshot is that if the enterprise has a large set of users and uses a predictable username policy, then the likelihood of a password spraying attack being successful is still significant when nKodes are used. However, as mentioned before, using nKodes (instead of PINs for instance) provides additional protection against password spraying in the case that the intruder does not observe the nKode keypad but is only able to send key sequence for login attempts since even the most commonly used passcodes would be permuted or scrambled.

### Password spraying for multiple logins:

Moreover, for a large database with $U$ sufficiently large one can imagine that password spraying would work on a large enough number $U'$ of users so that a round 2 of password spraying would also have a non-trivial chance of succeeding for some of the users. These probabilities go up if more than one failed attempt is allowed before freezing the user's account.

For example, 

### Guessing the passcode:

The likelihood that a randomly chosen passcode will yield a successful login no matter what shuffle has been applied, i.e. so that the attacker can successfully log in as many times as they want:
$1 / \text{Num}(\text{possible passcodes}).$

For example, when $k=m=10, p=7$ for $\ell = 4$ this probability is 

$(70)^{-4} \sim 4.16*10^{-8},$

 or about 4 chances in 100 million, and for $\ell = 6$ this probability is $(70)^{-6} \sim 8.5*10^{-12}$, or about 8.5 chances in 1 trillion.  

## Multiple Blind Attempts

The likelihood a blind attempt at a nKode on $k$ keys of length $\ell$  will successfully log in is $1/k^\ell$. 

For example, when $k=10$ for $\ell = 4$ this probability is $(10)^{-4}$, 1 chance in 10 thousand, and for $\ell = 6$ this probability is 1 chance in a million.  

The likelihood an $s$ blind attempts at an nKode on $k$ keys of length $\ell$ will successfully log in all $s$ times is $(1/k^\ell)^s$. 

For example, when $k=10$ for $\ell = 4$ and $s=2$ this probability is $((10)^{-4})^2 = 10^{-8}$, 1 chance in 100 million [4.16x less likely than just guessing the passcode directly], and for $\ell = 6$ this probability is $((10)^{-6})^2 = 10^{-12}$, or 1 chance in a trillion [8.5x less likely than just guessing the passcode directly].  

For example, when $k=10$ for $\ell = 4$ and $s=3$ this probability is $((10)^{-4})^3 = 10^{-12}$, [same order of magnitude as a passcode of length 6], and for $\ell = 6$ this probability is $((10)^{-6})^3 = 10^{-18}$, or 1 chance in one billion billion. 

## Incorrect nKodes that still work
We should also consider the number of nKodes that would yield a successful sequence of $s$ logins. [Add example]

## Longer passcodes might not always be more secure

This might be wrong, but let's investigate it anyway: Longer passcodes might not be more difficult to learn from observation. 
It may be possible to learn the split-shuffle from a pair of observations if the passcode is long enough. If the user learns the split-shuffle between attempt 1 and attempt 2, then they could obtain the entire nKode?

Thought experiment: 
User's nKode is [a,a,a,a,a,a,a... ] arbitrarily long, but uniform. If a ends up on key 1, then the user would type [1,1,1,1,...], but the attacker doesn't know which attribute was chosen to select key 1. 

User's nKode is [a,b,c,d,e,f,... ] arbitrarily long, but non-uniform. If a ends up on key 1, b on key 2, etc. then the user would type [1,2,3,4,...], which doesn't seem helpful, except the user eventually has to start repeating values for attributes, and those keys will be repeated. So this would lead to multiple observations of the shuffle function. In an $n$-letter alphabet, learning the values of $n-1$ distinct elements for a permutation is sufficient to learn the permutation. 

## Other notes

The intruder observes the entire keypad for each entry, not just the attributes on the keys that are entered. This can be useful in determining the split-shuffle. 

How much information does the intruder learn from an incorrect login (about the nKode and about the split-shuffle)?

How do you decide which attributes to shuffle? This selection should be randomized each time? Or perhaps having repetition makes it harder to determine the passcode because the intruder doesn't learn more information for that attribute.    

## Sideways attacks

### Time between keystrokes

If someone is able to observe the user typing the nKode, or record the keystrokes over time, then perhaps they could gain additional information about which kind of attribute is being searched for from the length of time between keystrokes.

### Eye tracking

Eye tracker on phone: How good would this need to be in order to see what attribute the user is searching for?

# Higher Complexity

## Dispersion
Dispersion is an operation on a keypad that permutes properties in such a way that 2 observations of the nKode are sufficient to learn the passcode. It does this by applying a distinct rotation to each property. The authors note that this is possible when the number of keys is not larger than the number of properties per key, because this ensures that there are enough distinct rotations so that no repetitions occur.  There are more general permutations that can also have this property, and it seems that this is already implemented in the Enrollment_Login_Renewal. 

## Split shuffle
Split shuffle attempts to avoid the dispersion permutation of the keypad so as to increase the number of times an intruder would have to observe the nKode being entered.

The properties are divided into 2 sets, each set will be shuffled by the same shuffle applied to all properties in that set of properties.

Note: by observing both keypads (before and after a split-shuffle), one can learn both what the split was, and what the two shuffles were.

We're intertested in studying how many observations an intruder must make in order to learn the passcode with the split shuffle in place. There are a few scenarios I can imagine. 

    * No split (analyzed above).
    * The split is determined once, and then the shuffles only happen on one side of the split.
    * The split changes every time randomly.
    * The split changes every time by a set strategy.

Of course we can consider these questions each time the metaparameters change. Recall,  
    * a $k$ digit keypad,
    * $p$ properties (position, central number, color, letter, emoji,...)
    * $m$ options for each property (\# positions, \# central numbers, \# colors, \# letters, \# emoji, ... ). typically  $m = k$.
    * $\ell$ = length of the passcode, which is a sequence of $\ell$ letters (options) selected from any of the options. 

Notice that when $k = 1$ the problem is nearly trivial. It doesn't matter what the properties are, the only thing the user is entering is $\ell$, and that can be observed in 1 try.

When $k = 2$. Here's the case $p = 2$ and a 4 letter passcode.

      
|key   | p0 | p1 |
|:----:|:--:|:--:|
|key 0 | a0 | b0 |
|key 1 | a1 | b1 |

After a shuffle [attribute 1]

|key   | p0 | p1 |
|:----:|:--:|:--:|
|key 0 | a0 | b1 |
|key 1 | a1 | b0 |

interaction:

|what |  |||||
|--------|--|--|--|--|--|
|Passcode| a0|b1|a1|b0|
|Display 1| 0|1|1|0|
|Display 2| 0|0|1|1|

The possible passcodes after display 1: 
0{a0,b0},1{a1,b1},1{a1,b1},0{a0,b0}

The possible passcodes after display 2: 
0{a0,b1},0{a0,b1},1{a1,b0},1{a1,b0}

Intersect:
{a0},{b1},{a1},{b0}
Passcode learned in 2.


When $k = 2$. Here's the case $p = 4$ and a 4 letter passcode.


|key   | p0 | p1 | p2 | p3 |
|:----:|:--:|:--:|:--:|:--:|
|key 0 | a0  | b0  | c0  | d0  |
|key 1 | a1  | b1  | c1  | d1  |

After a shuffle [attribute 1,2]

|key   | p0 | p1 | p2 | p3 |
|:----:|:--:|:--:|:--:|:--:|
|key 0 | a0  | b1  | c1  | d0  |
|key 1 | a1  | b0  | c0  | d1  |


interaction:

|what |  |||||
|--------|--|--|--|--|--|
|Passcode| a0|c1|c1|d0|
|Display 1| 0|1|1|0|
|Display 2| 0|0|0|0|

The possible passcodes after display 1: 
0{a0,b0,c0,d0},1{a1,b1,c1,d1},1{a1,b1,c1,d1},0{a0,b0,c0,d0}

The possible passcodes after display 2: 
0{a0,b1,c1,d0},0{a0,b1,c1,d0},0{a0,b1,c1,d0},0{a0,b1,c1,d0}

Intersect:
{a0,d0},{b1,c1},{b1,c1},{a0,d0}.

Passcode is not learned yet.

After a 3rd shuffle [attribute 1,3]

|key   | p0 | p1 | p2 | p3 |
|:----:|:--:|:--:|:--:|:--:|
|key 0 | a0  | b1  | c0  | d1  |
|key 1 | a1  | b0  | c1  | d0  |

|what |  |||||
|--------|--|--|--|--|--|
|Passcode| a0|c1|c1|d0|
|Display 1| 0|1|1|0|
|Display 2| 0|0|0|0|
|Display 3| 0|1|1|1|

The possible passcodes after display 3: 
0{a0,b1,c0,d1},1{a1,b0,c1,d0},1{a1,b0,c1,d0},1{a1,b0,c1,d0}

Intersect:
{a0},{c1},{c1},{d0}.

Passcode learned in 3.