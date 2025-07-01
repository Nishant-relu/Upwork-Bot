from .parsers import (
    JobCardParser, 
    ActivityParser, 
    ClientInfoParser, 
    AttachmentParser, 
    InvitationParser
)
from bs4 import Tag


class JobHtmlParser:
    @staticmethod
    def parse_job_card(card: Tag) -> dict | None:
        return JobCardParser.parse(card)

    @staticmethod
    def parse_activity(html: str) -> dict:
        return ActivityParser.parse(html)

    @staticmethod
    def parse_client_info(html: str) -> dict:
        return ClientInfoParser.parse(html)

    @staticmethod
    def parse_attachments(html: str) -> list:
        return AttachmentParser.parse(html)

    @staticmethod
    def parse_invitation_table(table_html: str) -> list:
        return InvitationParser.parse(table_html)
