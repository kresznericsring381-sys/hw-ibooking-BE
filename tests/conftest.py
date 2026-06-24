"""pytest 公共 fixture：Flask 测试客户端（需本地 MySQL 已导入 school 库）"""
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
