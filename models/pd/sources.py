from abc import ABC, abstractmethod
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr
from typing import Optional


class SourceABC(ABC, BaseModel):
    @property
    @abstractmethod
    def execution_json(self) -> dict:
        ...


class SourceGitSSH(SourceABC):
    repo: str
    private_key: str
    branch: Optional[str] = 'main'

    @property
    def execution_json(self):
        return {
            'git': {
                'repo': self.repo,
                'repo_branch': self.branch,
                'repo_key': self.private_key
            }
        }


class SourceGitHTTPS(SourceABC):
    repo: str
    branch: Optional[str] = 'main'
    username: Optional[str]
    password: Optional[str]

    @property
    def execution_json(self):
        return {
            'git': {
                'repo': self.repo,
                'repo_branch': self.branch
            }
        }


class SourceArtifact(SourceABC):
    file: str

    @property
    def execution_json(self):
        return {
            'artifact': self.file
        }


class SourceLocal(SourceABC):
    path: str

    @property
    def execution_json(self):
        return {
            'bucket': self.path
        }
