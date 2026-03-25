import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_without_files():
    """测试不带文件的聊天接口"""
    response = client.post(
        "/chat/",
        data={
            "message": "你好",
            "user_id": "test_user",
            "stream": "false"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_chat_with_csv_file():
    """测试上传CSV文件"""
    csv_content = b"name,age,city\nAlice,30,Beijing\nBob,25,Shanghai"
    
    response = client.post(
        "/chat/",
        data={
            "message": "请分析这个CSV文件",
            "user_id": "test_user",
            "stream": "false"
        },
        files={
            "files": ("test.csv", io.BytesIO(csv_content), "text/csv")
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploaded_files" in data
    assert len(data["uploaded_files"]) == 1
    assert data["uploaded_files"][0]["type"] == "csv"
    assert data["uploaded_files"][0]["original_name"] == "test.csv"


def test_chat_with_invalid_extension():
    """测试上传不支持的文件类型"""
    response = client.post(
        "/chat/",
        data={
            "message": "测试",
            "user_id": "test_user",
            "stream": "false"
        },
        files={
            "files": ("test.txt", io.BytesIO(b"test content"), "text/plain")
        }
    )
    
    assert response.status_code == 400
    assert "文件验证失败" in response.json()["detail"]


def test_chat_with_dangerous_filename():
    """测试危险文件名"""
    csv_content = b"name,age\nAlice,30"
    
    response = client.post(
        "/chat/",
        data={
            "message": "测试",
            "user_id": "test_user",
            "stream": "false"
        },
        files={
            "files": ("../../../etc/passwd.csv", io.BytesIO(csv_content), "text/csv")
        }
    )
    
    assert response.status_code == 400
    assert "文件验证失败" in response.json()["detail"]


def test_chat_with_empty_file():
    """测试空文件"""
    response = client.post(
        "/chat/",
        data={
            "message": "测试",
            "user_id": "test_user",
            "stream": "false"
        },
        files={
            "files": ("empty.csv", io.BytesIO(b""), "text/csv")
        }
    )
    
    assert response.status_code == 400
    assert "文件为空" in response.json()["detail"]


def test_chat_with_too_many_files():
    """测试上传过多文件"""
    csv_content = b"name,age\nAlice,30"
    
    files = [
        ("files", (f"test{i}.csv", io.BytesIO(csv_content), "text/csv"))
        for i in range(6)
    ]
    
    response = client.post(
        "/chat/",
        data={
            "message": "测试",
            "user_id": "test_user",
            "stream": "false"
        },
        files=files
    )
    
    assert response.status_code == 400
    assert "单次最多上传5个文件" in response.json()["detail"]


def test_chat_with_multiple_files():
    """测试上传多个文件"""
    csv_content = b"name,age\nAlice,30"
    
    files = [
        ("files", ("test1.csv", io.BytesIO(csv_content), "text/csv")),
        ("files", ("test2.csv", io.BytesIO(csv_content), "text/csv"))
    ]
    
    response = client.post(
        "/chat/",
        data={
            "message": "分析这些文件",
            "user_id": "test_user",
            "stream": "false"
        },
        files=files
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["uploaded_files"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
