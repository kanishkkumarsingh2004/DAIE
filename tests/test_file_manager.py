#!/usr/bin/env python3
"""
Tests for FileManagerTool operations on files and folders
"""

import os
import tempfile
import pytest
from daie.tools import FileManagerTool
from daie.tools.tool import ToolCategory


class TestFileManagerTool:
    """Test cases for FileManagerTool operations"""

    @pytest.fixture(scope="function")
    def temp_dir(self):
        """Create and clean up temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_file_manager_initialization(self):
        """Test FileManagerTool initialization"""
        tool = FileManagerTool()
        assert tool is not None
        assert tool.name == "file_manager"
        assert tool.category == ToolCategory.FILE
        assert tool.version == "1.0.0"

    def test_file_manager_metadata(self):
        """Test FileManagerTool metadata structure"""
        tool = FileManagerTool()
        metadata = tool.get_metadata_dict()
        assert metadata is not None
        assert isinstance(metadata, dict)
        assert len(metadata["parameters"]) > 0

    @pytest.mark.asyncio
    async def test_create_file(self, temp_dir):
        """Test file creation operation"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "test_file.txt")

        result = await tool.execute(
            {
                "action": "create_file",
                "path": file_path,
                "content": "Test content",
                "encoding": "utf-8",
            }
        )

        assert result["success"] is True
        assert os.path.exists(file_path)
        assert os.path.isfile(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert content == "Test content"

    @pytest.mark.asyncio
    async def test_create_directory(self, temp_dir):
        """Test directory creation operation"""
        tool = FileManagerTool()
        dir_path = os.path.join(temp_dir, "test_directory")

        result = await tool.execute({"action": "create_directory", "path": dir_path})

        assert result["success"] is True
        assert os.path.exists(dir_path)
        assert os.path.isdir(dir_path)

    @pytest.mark.asyncio
    async def test_read_file(self, temp_dir):
        """Test file reading operation"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "read_test.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Hello, World!")

        result = await tool.execute(
            {"action": "read_file", "path": file_path, "encoding": "utf-8"}
        )

        assert result["success"] is True
        assert result["content"] == "Hello, World!"
        assert result["encoding"] == "utf-8"

    @pytest.mark.asyncio
    async def test_write_file(self, temp_dir):
        """Test file writing operation"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "write_test.txt")

        result = await tool.execute(
            {
                "action": "write_file",
                "path": file_path,
                "content": "Write test content",
                "encoding": "utf-8",
            }
        )

        assert result["success"] is True
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == "Write test content"

    @pytest.mark.asyncio
    async def test_append_file(self, temp_dir):
        """Test file appending operation"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "append_test.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("First line\n")

        result = await tool.execute(
            {
                "action": "append_file",
                "path": file_path,
                "content": "Second line\n",
                "encoding": "utf-8",
            }
        )

        assert result["success"] is True
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "First line" in content
            assert "Second line" in content

    @pytest.mark.asyncio
    async def test_delete_file(self, temp_dir):
        """Test file deletion operation"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "delete_me.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Content to delete")

        result = await tool.execute({"action": "delete_file", "path": file_path})

        assert result["success"] is True
        assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_delete_directory(self, temp_dir):
        """Test directory deletion operation"""
        tool = FileManagerTool()
        dir_path = os.path.join(temp_dir, "delete_me_dir")
        os.makedirs(dir_path)

        result = await tool.execute({"action": "delete_directory", "path": dir_path})

        assert result["success"] is True
        assert not os.path.exists(dir_path)

    @pytest.mark.asyncio
    async def test_list_directory(self, temp_dir):
        """Test directory listing operation"""
        tool = FileManagerTool()
        dir_path = os.path.join(temp_dir, "list_dir")
        os.makedirs(dir_path)

        # Create test files
        file1 = os.path.join(dir_path, "file1.txt")
        file2 = os.path.join(dir_path, "file2.txt")
        subdir = os.path.join(dir_path, "subdir")

        with open(file1, "w", encoding="utf-8") as f:
            f.write("File 1 content")

        with open(file2, "w", encoding="utf-8") as f:
            f.write("File 2 content")

        os.makedirs(subdir)

        # Test listing contents
        result = await tool.execute(
            {
                "action": "list_contents",
                "path": dir_path,
                "recursive": True,
                "include_hidden": False,
            }
        )

        assert result["success"] is True
        assert len(result["contents"]) == 3  # 2 files + 1 directory

        # Verify all items are listed
        item_names = [item["name"] for item in result["contents"]]
        assert "file1.txt" in item_names
        assert "file2.txt" in item_names
        assert "subdir" in item_names

    @pytest.mark.asyncio
    async def test_copy_file(self, temp_dir):
        """Test file copying operation"""
        tool = FileManagerTool()
        src_path = os.path.join(temp_dir, "source_file.txt")
        dest_path = os.path.join(temp_dir, "destination_file.txt")

        with open(src_path, "w", encoding="utf-8") as f:
            f.write("Content to copy")

        result = await tool.execute(
            {"action": "copy_file", "path": src_path, "destination": dest_path}
        )

        assert result["success"] is True
        assert os.path.exists(dest_path)

        with open(dest_path, "r", encoding="utf-8") as f:
            assert f.read() == "Content to copy"

    @pytest.mark.asyncio
    async def test_copy_directory(self, temp_dir):
        """Test directory copying operation"""
        tool = FileManagerTool()
        src_dir = os.path.join(temp_dir, "src_dir")
        dest_dir = os.path.join(temp_dir, "dest_dir")

        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "file.txt"), "w", encoding="utf-8") as f:
            f.write("Test file")

        result = await tool.execute(
            {"action": "copy_directory", "path": src_dir, "destination": dest_dir}
        )

        assert result["success"] is True
        assert os.path.exists(dest_dir)
        assert os.path.exists(os.path.join(dest_dir, "file.txt"))

    @pytest.mark.asyncio
    async def test_move_file(self, temp_dir):
        """Test file moving/renaming operation"""
        tool = FileManagerTool()
        src_path = os.path.join(temp_dir, "old_name.txt")
        dest_path = os.path.join(temp_dir, "new_name.txt")

        with open(src_path, "w", encoding="utf-8") as f:
            f.write("Content to move")

        result = await tool.execute(
            {"action": "move_file", "path": src_path, "destination": dest_path}
        )

        assert result["success"] is True
        assert not os.path.exists(src_path)
        assert os.path.exists(dest_path)

    @pytest.mark.asyncio
    async def test_file_exists(self, temp_dir):
        """Test file existence check"""
        tool = FileManagerTool()
        existing_path = os.path.join(temp_dir, "existing_file.txt")
        non_existing_path = os.path.join(temp_dir, "non_existing_file.txt")

        with open(existing_path, "w", encoding="utf-8") as f:
            f.write("Content")

        existing_result = await tool.execute(
            {"action": "file_exists", "path": existing_path}
        )

        non_existing_result = await tool.execute(
            {"action": "file_exists", "path": non_existing_path}
        )

        assert existing_result["exists"] is True
        assert non_existing_result["exists"] is False

    @pytest.mark.asyncio
    async def test_directory_exists(self, temp_dir):
        """Test directory existence check"""
        tool = FileManagerTool()
        existing_path = os.path.join(temp_dir, "existing_dir")
        non_existing_path = os.path.join(temp_dir, "non_existing_dir")

        os.makedirs(existing_path)

        existing_result = await tool.execute(
            {"action": "directory_exists", "path": existing_path}
        )

        non_existing_result = await tool.execute(
            {"action": "directory_exists", "path": non_existing_path}
        )

        assert existing_result["exists"] is True
        assert non_existing_result["exists"] is False

    @pytest.mark.asyncio
    async def test_get_file_info(self, temp_dir):
        """Test getting file information"""
        tool = FileManagerTool()
        file_path = os.path.join(temp_dir, "info_test.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Test content" * 100)

        result = await tool.execute({"action": "get_file_info", "path": file_path})

        assert result["success"] is True
        assert result["path"] == file_path
        assert result["size"] > 0
        assert result["is_file"] is True
        assert result["is_dir"] is False
        assert isinstance(result["created"], float)
        assert isinstance(result["modified"], float)

    @pytest.mark.asyncio
    async def test_get_directory_info(self, temp_dir):
        """Test getting directory information"""
        tool = FileManagerTool()
        dir_path = os.path.join(temp_dir, "dir_info_test")

        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "file1.txt"), "w", encoding="utf-8") as f:
            f.write("File content")

        with open(os.path.join(dir_path, "file2.txt"), "w", encoding="utf-8") as f:
            f.write("Another file")

        os.makedirs(os.path.join(dir_path, "subdir"))

        result = await tool.execute({"action": "get_directory_info", "path": dir_path})

        assert result["success"] is True
        assert result["path"] == dir_path
        assert result["file_count"] == 2
        assert result["directory_count"] == 1
        assert result["total_items"] == 3
        assert result["is_file"] is False
        assert result["is_dir"] is True
        assert isinstance(result["created"], float)
        assert isinstance(result["modified"], float)

    @pytest.mark.asyncio
    async def test_nonexistent_operations(self, temp_dir):
        """Test operations on nonexistent paths"""
        tool = FileManagerTool()
        nonexistent_file = os.path.join(temp_dir, "nonexistent_file.txt")
        nonexistent_dir = os.path.join(temp_dir, "nonexistent_dir")

        # Read from nonexistent file should raise exception
        with pytest.raises(Exception):
            await tool.execute({"action": "read_file", "path": nonexistent_file})

        # Delete nonexistent file should not raise exception but return success: False
        delete_result = await tool.execute(
            {"action": "delete_file", "path": nonexistent_file}
        )
        assert delete_result["success"] is False
        assert "File does not exist" in delete_result["message"]

        # List nonexistent directory should raise exception
        with pytest.raises(Exception):
            await tool.execute({"action": "list_contents", "path": nonexistent_dir})

    @pytest.mark.asyncio
    async def test_incorrect_path_types(self, temp_dir):
        """Test operations on incorrect path types (file as directory and vice versa)"""
        tool = FileManagerTool()

        file_path = os.path.join(temp_dir, "not_a_dir.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Content")

        with pytest.raises(Exception):
            await tool.execute({"action": "list_contents", "path": file_path})

        dir_path = os.path.join(temp_dir, "not_a_file_dir")
        os.makedirs(dir_path)

        with pytest.raises(Exception):
            await tool.execute({"action": "read_file", "path": dir_path})

    @pytest.mark.asyncio
    async def test_recursive_operations(self, temp_dir):
        """Test recursive operations on directories with contents"""
        tool = FileManagerTool()
        dir_path = os.path.join(temp_dir, "recursive_dir")
        subdir_path = os.path.join(dir_path, "subdir")

        os.makedirs(subdir_path)

        with open(os.path.join(dir_path, "file1.txt"), "w", encoding="utf-8") as f:
            f.write("File 1")

        with open(os.path.join(subdir_path, "file2.txt"), "w", encoding="utf-8") as f:
            f.write("File 2")

        delete_result = await tool.execute(
            {"action": "delete_directory", "path": dir_path, "recursive": True}
        )

        assert delete_result["success"] is True
        assert not os.path.exists(dir_path)

    @pytest.mark.asyncio
    async def test_toolkit(self):
        """Test FileManagerToolkit functionality"""
        from daie.tools import FileManagerToolkit

        toolkit = FileManagerToolkit()

        assert hasattr(toolkit, "get_tools")
        assert callable(getattr(toolkit, "get_tools"))

        tools = toolkit.get_tools()
        assert len(tools) == 1
        assert isinstance(tools[0], FileManagerTool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
