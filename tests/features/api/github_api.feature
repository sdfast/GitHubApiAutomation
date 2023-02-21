Feature: Github API Automation

  Scenario: Test Github Flow
    Given user logs in to GitHub using basic authentication
    When user creates repository with name "git_flow_first_task"
    And user creates branch "feature/git_flow_feature"
    And user commits auto generated file to branch "feature/git_flow_feature"
    And user creates pull request to main branch
    Then commit messages are maximum "50" characters and match pattern "[AAA-1234] text"