# Code demonstration for the paper presentation


## A quick example using prolog

- Install swi-prolog (lates version works).
- run `swipl` to launch the swi prolog environment.
- consult the example prolog file 

```
?- [prolog_demo].
```

Result should show ```true.```


## A quick proof using LeanCoP

- Install swi-prolog (lates version works).
- Download and unzip leancop_swi.tar.gz 2.1 (http://www.leancop.de/leancopS.html#leancop10).
- Go to the unzipped leancop folder.
- run `swipl` to launch the swi prolog environment.
- consult the leancop prolog file 

```
?- [leancop21_swi].
```

- Run a proof (if p is true, and for all X, p implies q(X), then for all Y, q(Y) is true)

```
?- P = ((p,all X:(p=>q(X)))=>all Y:q(Y)), prove(P, Proof ).
```

- output should look like:

```
Proof = [[#, q(1^[])], [[-q(1^[]), p], [[-p]]]].
```

Which looks like this:

       q
     /   \
    !q    p
          /
        !p
