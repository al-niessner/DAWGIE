
# How to contribute software development to this project

## Philosophy

The idea of this contribution methodology is to use well-defined and encapsulated problems (acheivable milestones) to march to a goal as opposed to opened ended problems and roaming around. While this methodology should be adhered to always, as with PEP-8, within reason.

The keystone of the methodology is working with well-defined and encapsulated problems in the issue system for defining code changes. Well-defined and encapsulated problems can be identified because they can be tested with a unit test. Therefore, the first of any issue is to identify the problem space and the unit test for that problem space. If the problem space is so large that single unit test is insufficient, then subordinate issues should be generated until a unit test can be identified.

Rules for defining a unit test are mostly ripped from [Hitchhiker's Guide to Python: Testing Your Code](http://docs.python-guide.org/en/latest/writing/tests/):

* A testing unit should focus on one tiny bit of functionality and prove it correct.
* Each test unit must be fully independent. Each test must be able to run alone, and also within the test suite, regardless of the order that they are called. The implication of this rule is that each test must be loaded with a fresh dataset and may have to do some cleanup afterwards. This is usually handled by setUp() and tearDown() methods.
* Always run the full test suite before a coding session, and run it again after. This will give you more confidence that you did not break anything in the rest of the code.
* If you are in the middle of a development session and have to interrupt your work, it is a good idea to write a broken unit test about what you want to develop next. When coming back to work, you will have a pointer to where you were and get back on track faster.
* Have a negative test for each of the branches in the unit. Using postive and negative tests exercise and verify both the then and else blocks of conditionals.

### General Information

1. Unit tests should be done in the form of nUnit.
    1. `cppunit` for C/C++
    1. `JUnit` for Java
    1. `unittest` for Python
1. Unit tests should not require any data from the file system.

### New Feature

1. New features should start with an issue that is tagged 'question' and maybe 'help wanted'. These are open-ended issues that generate discussion but should __never__ generate a branch and pull request.
1. If ideas emerge that require investigation, then an issue tagged `investigation` should be used to track the information learned and reasons for decisions.
1. As the discussion progresses, it should generate well-defined and encapsulated problem issues tagged with 'enhancement' along with the elements it changes. These issues should generate a issues that generate a branch and pull request.
    1. Implement a unit test of the expected behavior.
        1. Implement a positive check.
        1. Implement a negative check.
    1. Implement the enhancement.
    1. Correct the unit test with behavioral changes during previous step.
        1. Implement a negative check for each branch in the enhancement.
1. Once all of the subordinate issues tagged 'enhancement' are closed, an "integration" test should be performed to insure all of the parts work together properly.
1. The initial issue tagged 'question' can be closed now.

### Bug Identification and Correction

1. An issue should be generated discribing the discrepency between the expected and experienced behaviors.
1. A unit test should be discussed to show show the failure. If the bug was discovered during any form of testing, the steps that lead to the bug discovry should be part of the discussion.
1. A branch and pull request should be generated with the first code changes being the new unit test.
1. The code should be changed to fix the bug:
    1. If the test still fails, undo the changes and try again.
    1. If the test passes, close the issue

## Mechanics

1. `fork` the repository. This step is done once when a developer decides to contribute software development effort to this project.

Repeat the following steps for each contribution noting that the first step is often already accomplished:
1. Create an `issue` for work to be done on the original repository. Follow the philosophy and create issues that are well-defined and encapsulated problems.
1. Create a `branch` whose name is `issue_#` where `#` is the issue number from previous step. It will allow everyone to see what changes were needed to accomplish the work described in the issue.
1. Open a `pull request` between the working repository and the forked repository with the working branch from the previous step. A change has to exist in the working branch to open the `pull request`. The `pull request` will manage when the changes are allowed to be accepted back into the original work. There will always be some temptation to wait to open the `pull request` until all the work is done, but the temptation is not valid. Even making a minor change then opening the `pull request` is far better because it starts the conversation earlier making it more likely for the `pull request` to be accepted.
1. With the `pull request` open, augment the required reviewers with any others that would be helpful.
1. With the `pull request` open and conversation started, use the continuous integration (CI) steps to meet the projects requirements for acceptance. Every time a push occurs to the `pull request`. the CI tools will check the following:
    1. Coding standards: all of the code will be checked that it meets the projects basic coding standards, like PEP-8 for Python.
    1. Static Analysis: all of the code is scanned for simple coding errors, like pylint for Python or Coverity for C++.
    1. Unit Testing: run unit tests to verify code is still executable and prevent bug regression, like pytest for Python.
    1. Coverage: verify modified code is also unit tested. Full coverage comes with time, but requires that bugs are proven fixed and stay fixed.
1. Once the automated checks and reviewers have accepted the`pull request`, `merge` the `pull request` back into the original repository and then `delete` the branch. Cleaning up afterward reduces confusion for new developers that arrive (do not see a thousand branches) and helps to enforce small, encapsulated work that will march to a goal rather than roam in an open ended problem space that never finishes.

These mechanics keep the master branch in a stable and ready-to-use condition at all times.
