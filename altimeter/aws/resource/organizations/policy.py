""" Resource representing a Policy as viewed in Orgs. """
from typing import Type

from botocore.client import BaseClient

from altimeter.aws.resource.organizations import OrganizationsResourceSpec
from altimeter.aws.resource.organizations.org import OrgResourceSpec
from altimeter.aws.resource.resource_spec import ListFromAWSResult
from altimeter.aws.resource.util import policy_doc_dict_to_sorted_str
from altimeter.core.graph.field.list_field import AnonymousListField
from altimeter.core.graph.field.resource_link_field import ResourceLinkField
from altimeter.core.graph.field.scalar_field import ScalarField
from altimeter.core.graph.schema import Schema


class BaseOrgPolicyResourceSpec(OrganizationsResourceSpec):
    """ Resource representing an AWS Organizations Policy.

    https://docs.aws.amazon.com/organizations/latest/APIReference/API_Policy.html
    """
    type_name = "policy"
    parallel_scan = True
    schema = Schema(
        ScalarField("Name"),
        ScalarField("Id"),
        ScalarField("Type"),
        ScalarField("Description"),
        ScalarField("AwsManaged"),
        ScalarField("Content")
    )
    policy_type = None

    @classmethod
    def list_from_aws(
            cls: Type["OrgPolicyResourceSpec"], client: BaseClient, account_id: str, region: str
    ) -> ListFromAWSResult:
        """Return a dict of dicts of the format:

            {'policy_1_arn': {policy_1_dict},
             'policy_2_arn': {policy_2_dict},
             ...}

        Where the dicts represent results from list_policies and additional info per resource target by
        list_policies_for_target."""

        if cls.policy_type is None:
            raise NotImplemented("Set the policy_type to use this class properly")

        policies = {}
        paginator = client.get_paginator("list_policies")

        for resp in paginator.paginate(Filter=cls.policy_type):
            for policy in resp.get("Policies", []):
                resource_arn = policy["Arn"]

                # To get the policy content, we need to describe the policy
                # TODO: Wrap this in useful exception handling...
                describe_policy_resp = client.describe_policy(PolicyId=policy.get("Id"))
                if "Policy" in describe_policy_resp:
                    policy["Content"] = policy_doc_dict_to_sorted_str(
                        describe_policy_resp["Policy"]["Content"]
                    )

                # Add the policy to the collection
                policies[resource_arn] = policy

        # Return the result
        return ListFromAWSResult(resources=policies)


class AIOptOutOrgPolicyResourceSpec(BaseOrgPolicyResourceSpec):
    policy_type = "AISERVICES_OPT_OUT_POLICY"


class BackupOrgPolicyResourceSpec(BaseOrgPolicyResourceSpec):
    policy_type = "BACKUP_POLICY"


class SCPOrgPolicyResourceSpec(BaseOrgPolicyResourceSpec):
    policy_type = "SERVICE_CONTROL_POLICY"


class TaggingOrgPolicyResourceSpec(BaseOrgPolicyResourceSpec):
    policy_type = "TAG_POLICY"
