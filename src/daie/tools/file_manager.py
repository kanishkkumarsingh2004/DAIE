"""
File and folder management tool using CED (Create-Edit-Delete) operations
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from daie.tools.tool import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class FileManagerTool(Tool):
    """
    A tool for managing files and folders using Create-Edit-Delete operations.
    
    This tool supports various file and directory operations including:
    - Creating files and directories
    - Reading, writing, and editing files
    - Deleting files and directories
    - Listing directory contents
    - Copying and moving files/directories
    - Checking file/directory existence and properties
    """
    
    def __init__(self):
        metadata = ToolMetadata(
            name="file_manager",
            description="Manage files and folders using Create-Edit-Delete operations",
            category=ToolCategory.FILE,
            version="1.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=[
                "file_management",
                "create",
                "edit",
                "delete",
                "read",
                "write",
                "copy",
                "move",
                "list",
                "directory",
                "filesystem"
            ],
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="File management operation to perform",
                    required=True,
                    default="list",
                    choices=[
                        "create_file",
                        "create_directory",
                        "read_file",
                        "write_file",
                        "append_file",
                        "delete_file",
                        "delete_directory",
                        "list_contents",
                        "copy_file",
                        "copy_directory",
                        "move_file",
                        "move_directory",
                        "file_exists",
                        "directory_exists",
                        "get_file_info",
                        "get_directory_info"
                    ]
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to file or directory for operation",
                    required=True,
                    default=None
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write or append to file",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="destination",
                    type="string",
                    description="Destination path for copy or move operations",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="File encoding for read/write operations",
                    required=False,
                    default="utf-8"
                ),
                ToolParameter(
                    name="recursive",
                    type="boolean",
                    description="Recursively perform operation on directories",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="include_hidden",
                    type="boolean",
                    description="Include hidden files/directories in listings",
                    required=False,
                    default=False
                )
            ]
        )
        super().__init__(metadata)
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file management operations
        
        Args:
            params: Parameters for the operation
            
        Returns:
            Dictionary containing operation results
            
        Raises:
            Exception: If operation fails
        """
        try:
            action = params.get("action")
            path = params.get("path")
            
            if not path:
                raise Exception("Path parameter is required")
                
            path_obj = Path(path)
            
            if action == "create_file":
                return self._create_file(path_obj, params)
            elif action == "create_directory":
                return self._create_directory(path_obj, params)
            elif action == "read_file":
                return self._read_file(path_obj, params)
            elif action == "write_file":
                return self._write_file(path_obj, params)
            elif action == "append_file":
                return self._append_file(path_obj, params)
            elif action == "delete_file":
                return self._delete_file(path_obj, params)
            elif action == "delete_directory":
                return self._delete_directory(path_obj, params)
            elif action == "list_contents":
                return self._list_contents(path_obj, params)
            elif action == "copy_file":
                return self._copy_file(path_obj, params)
            elif action == "copy_directory":
                return self._copy_directory(path_obj, params)
            elif action == "move_file":
                return self._move_file(path_obj, params)
            elif action == "move_directory":
                return self._move_directory(path_obj, params)
            elif action == "file_exists":
                return {"exists": path_obj.is_file()}
            elif action == "directory_exists":
                return {"exists": path_obj.is_dir()}
            elif action == "get_file_info":
                return self._get_file_info(path_obj)
            elif action == "get_directory_info":
                return self._get_directory_info(path_obj)
            else:
                raise Exception(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            raise
    
    def _create_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file"""
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            content = params.get("content", "")
            encoding = params.get("encoding", "utf-8")
            
            with open(path_obj, 'w', encoding=encoding) as f:
                f.write(content)
                
            logger.info(f"File created: {path_obj}")
            return {
                "success": True,
                "path": str(path_obj),
                "size": path_obj.stat().st_size,
                "message": "File created successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to create file: {e}")
    
    def _create_directory(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new directory"""
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {path_obj}")
            return {
                "success": True,
                "path": str(path_obj),
                "message": "Directory created successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to create directory: {e}")
    
    def _read_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        if not path_obj.is_file():
            raise Exception(f"Path does not exist or is not a file: {path_obj}")
            
        try:
            encoding = params.get("encoding", "utf-8")
            content = path_obj.read_text(encoding=encoding)
            
            return {
                "success": True,
                "path": str(path_obj),
                "encoding": encoding,
                "size": path_obj.stat().st_size,
                "content": content
            }
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")
    
    def _write_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to file"""
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            content = params.get("content", "")
            encoding = params.get("encoding", "utf-8")
            
            with open(path_obj, 'w', encoding=encoding) as f:
                f.write(content)
                
            logger.info(f"File written: {path_obj}")
            return {
                "success": True,
                "path": str(path_obj),
                "encoding": encoding,
                "size": path_obj.stat().st_size,
                "message": "File written successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to write file: {e}")
    
    def _append_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append to file"""
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            content = params.get("content", "")
            encoding = params.get("encoding", "utf-8")
            
            with open(path_obj, 'a', encoding=encoding) as f:
                f.write(content)
                
            logger.info(f"File appended: {path_obj}")
            return {
                "success": True,
                "path": str(path_obj),
                "encoding": encoding,
                "size": path_obj.stat().st_size,
                "message": "File appended successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to append file: {e}")
    
    def _delete_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete file"""
        if not path_obj.exists():
            return {
                "success": False,
                "path": str(path_obj),
                "message": "File does not exist"
            }
            
        if not path_obj.is_file():
            raise Exception(f"Path is not a file: {path_obj}")
            
        try:
            path_obj.unlink()
            logger.info(f"File deleted: {path_obj}")
            return {
                "success": True,
                "path": str(path_obj),
                "message": "File deleted successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to delete file: {e}")
    
    def _delete_directory(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete directory"""
        if not path_obj.exists():
            return {
                "success": False,
                "path": str(path_obj),
                "message": "Directory does not exist"
            }
            
        if not path_obj.is_dir():
            raise Exception(f"Path is not a directory: {path_obj}")
            
        try:
            recursive = params.get("recursive", False)
            if recursive:
                import shutil
                shutil.rmtree(path_obj)
                logger.info(f"Directory deleted recursively: {path_obj}")
            else:
                path_obj.rmdir()
                logger.info(f"Directory deleted: {path_obj}")
                
            return {
                "success": True,
                "path": str(path_obj),
                "recursive": recursive,
                "message": "Directory deleted successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to delete directory: {e}")
    
    def _list_contents(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents"""
        if not path_obj.exists():
            raise Exception(f"Directory does not exist: {path_obj}")
            
        if not path_obj.is_dir():
            raise Exception(f"Path is not a directory: {path_obj}")
            
        try:
            include_hidden = params.get("include_hidden", False)
            recursive = params.get("recursive", False)
            
            contents = []
            for item in path_obj.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                    
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "is_file": item.is_file(),
                    "size": item.stat().st_size if item.is_file() else None
                }
                
                if recursive and item.is_dir():
                    item_info["children"] = self._list_contents(item, params)["contents"]
                    
                contents.append(item_info)
                
            return {
                "success": True,
                "path": str(path_obj),
                "recursive": recursive,
                "include_hidden": include_hidden,
                "contents": contents,
                "total_items": len(contents)
            }
        except Exception as e:
            raise Exception(f"Failed to list directory contents: {e}")
    
    def _copy_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy file"""
        destination = params.get("destination")
        if not destination:
            raise Exception("Destination path is required for copy operation")
            
        if not path_obj.is_file():
            raise Exception(f"Source path is not a file: {path_obj}")
            
        try:
            dest_obj = Path(destination)
            dest_obj.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(path_obj, dest_obj)
            
            logger.info(f"File copied: {path_obj} -> {dest_obj}")
            return {
                "success": True,
                "source": str(path_obj),
                "destination": str(dest_obj),
                "size": dest_obj.stat().st_size,
                "message": "File copied successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to copy file: {e}")
    
    def _copy_directory(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy directory"""
        destination = params.get("destination")
        if not destination:
            raise Exception("Destination path is required for copy operation")
            
        if not path_obj.is_dir():
            raise Exception(f"Source path is not a directory: {path_obj}")
            
        try:
            dest_obj = Path(destination)
            dest_obj.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copytree(path_obj, dest_obj, dirs_exist_ok=True)
            
            logger.info(f"Directory copied: {path_obj} -> {dest_obj}")
            return {
                "success": True,
                "source": str(path_obj),
                "destination": str(dest_obj),
                "message": "Directory copied successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to copy directory: {e}")
    
    def _move_file(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move file"""
        destination = params.get("destination")
        if not destination:
            raise Exception("Destination path is required for move operation")
            
        if not path_obj.is_file():
            raise Exception(f"Source path is not a file: {path_obj}")
            
        try:
            dest_obj = Path(destination)
            dest_obj.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.move(path_obj, dest_obj)
            
            logger.info(f"File moved: {path_obj} -> {dest_obj}")
            return {
                "success": True,
                "source": str(path_obj),
                "destination": str(dest_obj),
                "message": "File moved successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to move file: {e}")
    
    def _move_directory(self, path_obj: Path, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move directory"""
        destination = params.get("destination")
        if not destination:
            raise Exception("Destination path is required for move operation")
            
        if not path_obj.is_dir():
            raise Exception(f"Source path is not a directory: {path_obj}")
            
        try:
            dest_obj = Path(destination)
            dest_obj.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.move(path_obj, dest_obj)
            
            logger.info(f"Directory moved: {path_obj} -> {dest_obj}")
            return {
                "success": True,
                "source": str(path_obj),
                "destination": str(dest_obj),
                "message": "Directory moved successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to move directory: {e}")
    
    def _get_file_info(self, path_obj: Path) -> Dict[str, Any]:
        """Get file information"""
        if not path_obj.is_file():
            raise Exception(f"Path is not a file: {path_obj}")
            
        try:
            stat = path_obj.stat()
            return {
                "success": True,
                "path": str(path_obj),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "access_time": stat.st_atime,
                "is_file": True,
                "is_dir": False
            }
        except Exception as e:
            raise Exception(f"Failed to get file info: {e}")
    
    def _get_directory_info(self, path_obj: Path) -> Dict[str, Any]:
        """Get directory information"""
        if not path_obj.is_dir():
            raise Exception(f"Path is not a directory: {path_obj}")
            
        try:
            stat = path_obj.stat()
            file_count = 0
            dir_count = 0
            
            for item in path_obj.iterdir():
                if item.is_file():
                    file_count += 1
                elif item.is_dir():
                    dir_count += 1
                    
            return {
                "success": True,
                "path": str(path_obj),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "access_time": stat.st_atime,
                "is_file": False,
                "is_dir": True,
                "file_count": file_count,
                "directory_count": dir_count,
                "total_items": file_count + dir_count
            }
        except Exception as e:
            raise Exception(f"Failed to get directory info: {e}")


class FileManagerToolkit:
    """
    Collection of file management tools for easy access
    """
    
    @staticmethod
    def get_tools() -> list:
        """
        Get all file management tools
        
        Returns:
            List of file management tool instances
        """
        return [FileManagerTool()]
