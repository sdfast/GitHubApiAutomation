import re
import json
import pandas as pd
import time

from pytest_bdd import scenario, given, when, then
from pytest_bdd import parsers
from pathlib import Path
from utils.utilities import create_file_and_return_its_path, get_file_content_base64
from utils.auth import BasicAuth

feature_file_dir = "../features/api"
feature_file_name = "github_api.feature"
BASE_DIR = Path(__file__).resolve().parent
FEATURE_FILE = BASE_DIR.joinpath(feature_file_dir).joinpath(feature_file_name)


@scenario(str(FEATURE_FILE), "Github Flow")
def test_github_flow():
    print(f"Finishing tests")
    pass


@given('user logs in to GitHub using basic authentication')
def auth_github_basic(context):
    context["BasicAuth"] = BasicAuth(
        user=context["github_user"],
        token=context["github_token"]
    )
    base_api_url = context["base_api_url"]
    response = context["BasicAuth"].session.get(f"{base_api_url}/users/" + context["github_user"])

    assert response.status_code == 200
    assert response.json()['login'] == context["github_user"]
    assert response.json()['name'] == context["account_info"]["name"]
    assert response.json()['bio'] == context["account_info"]["bio"]


@given(parsers.parse('user creates repository with name "{repo_name}"'))
@when(parsers.parse('user creates repository with name "{repo_name}"'))
def create_repository(repo_name, context):
    context["repo_name"] = repo_name
    context["BasicAuth"].session.headers.update(
        {"Authorization": "token " + context["github_token"],
         "Accept": "application/vnd.github.v3+json"}
    )

    create_repo_response = context["BasicAuth"].session.post(
        url="https://api.github.com/user/repos",
        data=json.dumps(
            {"name": repo_name,
             "auto_init": True}
        )
    )
    context["base_url"] = "https://api.github.com/repos/" + context["github_user"] + "/" + context["repo_name"]

    assert create_repo_response.status_code == 201
    assert create_repo_response.json()['url'] == context["base_url"]

    get_repo_response = context["BasicAuth"].session.get(url=context["base_url"])

    assert get_repo_response.status_code == 200


@when(parsers.parse('user creates branch "{branch_name}"'))
def create_branch(context, branch_name):
    context["branch_name"] = branch_name
    branches = context["BasicAuth"].session.get(context["base_url"] + "/git/refs/heads").json()

    counter = 0
    while branches is None:
        time.sleep(0.1)
        counter += 1
        if counter == 20:
            break

    context['last_tree_sha'] = branches[-1]['object']['sha']

    payload = json.dumps(
        {
            "ref": "refs/heads/" + context["branch_name"],
            "sha": context['last_tree_sha']
        }
    )

    create_branch_response = context["BasicAuth"].session.post(
        url=context["base_url"] + "/git/refs", data=payload)

    assert create_branch_response.status_code == 201, f"Response: {create_branch_response.text}"

    list_branches_response = context["BasicAuth"].session.get(context["base_url"] + "/branches")

    assert list_branches_response.status_code == 200
    assert list_branches_response.json()[0]['name'] == context["branch_name"]


@when(parsers.parse('user commits auto generated file to branch "{branch_name}"'))
def commit_file(context, branch_name):
    commit_file_info = create_file_and_return_its_path()
    context['commit_file_path'] = commit_file_info['file_path']
    file_content = str(get_file_content_base64(commit_file_info['file_path']))
    base_url = context["base_url"]

    put_payload = json.dumps(
        {
            "message": "[AAA-0001] Add automatically generated file: " + commit_file_info['file_name'],
            "author": {"name": "sdfast", "email": "sdfast@o2.pl"},
            "content": file_content,
            "branch": branch_name
        }
    )

    commit_file_request = context["BasicAuth"].session.put(
        url=base_url + "/contents/" + commit_file_info["file_name"],
        data=put_payload
    )

    assert commit_file_request.status_code == 201

    file_name = commit_file_request.json()["content"]["name"]
    file_url = commit_file_request.json()["content"]["url"]

    get_file_request = context["BasicAuth"].session.get(url=file_url)

    assert get_file_request.status_code == 200
    assert get_file_request.json()["name"] == file_name


@when('user creates pull request to main branch')
def create_pull_request(context):
    pr_title = "git_flow_feature"

    create_pr_payload = json.dumps(
        {
            "title": pr_title,
            "head": context["github_user"] + ":" + context["branch_name"],
            "base": "main"
        }
    )

    create_pr_request = context["BasicAuth"].session.post(
        url=context["base_url"] + "/pulls",
        data=create_pr_payload
    )

    context['pr_number'] = str(create_pr_request.json()["number"])

    assert create_pr_request.status_code == 201

    get_pr_request = context["BasicAuth"].session.get(context["base_url"] + "/pulls/" + context['pr_number'])

    assert get_pr_request.status_code == 200
    assert get_pr_request.json()['title'] == pr_title


@then(parsers.parse('commit messages are maximum "{char_limit}" characters and match pattern "{pattern}"'))
def commits_match_length_and_pattern(context, char_limit, pattern):
    get_branches_request = context["BasicAuth"].session.get(url=context["base_url"] + "/branches")
    regex = r'\[[A-Z]{3}-\d{4}\]\s'

    assert re.search(regex, pattern) is not None

    commits_urls = []
    for branch in get_branches_request.json():
        commits_urls.append(branch["commit"]["url"])

    commits_messages = []
    initial_commit_count = 0
    for url in commits_urls:
        message = context["BasicAuth"].session.get(url=url).json()["commit"]["message"]
        if message == "Initial commit":
            initial_commit_count += 1

        if message != "Initial commit":
            commits_messages.append(message)

    assert initial_commit_count == 1, f"There should be only '1' but are {initial_commit_count}"

    validation_results = []
    for message in commits_messages:
        validation_success = False
        if re.search(regex, message) is not None and len(message) >= int(char_limit):
            validation_success = True
        validation_results.append({'message': message, 'validation_success': validation_success})

    test_result_df = pd.DataFrame(validation_results, columns=['message', 'validation_success'])

    assert (False in set(test_result_df['validation_success'])) is False
