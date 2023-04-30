% Fact
friend(alice, bob).

% Rule
is_friend(X, Y) :- friend(X, Y); friend(Y, X).

% Query
% ?- is_friend(alice, bob).