import React from "react"
import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import FileBrowser, {
  Icons,
  FileBrowserFile,
  FileBrowserFolder,
} from "react-keyed-file-browser"

import get from "lodash.get"
import IframeResizer from "iframe-resizer-react"
import Actions from "./actions"
import type { IActionsProps } from "./actions"

import "react-keyed-file-browser/dist/react-keyed-file-browser.css"
import "font-awesome/css/font-awesome.min.css"

interface File {
  path: string
  name?: string
  size?: number
  create_time?: number
  update_time?: number
  access_time?: number
}

interface Folder {
  path: string
  name?: string
}

enum StreamlitEventType {
  SELECT_FILE = "SELECT_FILE",
  SELECT_FOLDER = "SELECT_FOLDER",
  DOWNLOAD = "DOWNLOAD",
  DELETE_FILE = "DELETE_FILE",
  DELETE_FOLDER = "DELETE_FOLDER",
  RENAME_FOLDER = "RENAME_FOLDER",
  RENAME_FILE = "RENAME_FILE",
  CREATE_FILE = "CREATE_FILE",
  CREATE_FOLDER = "CREATE_FOLDER",
  MOVE_FILE = "MOVE_FILE",
  MOVE_FOLDER = "MOVE_FOLDER",
  CHOOSE_FILE = "CHOOSE_FILE",
  CHOOSE_FOLDER = "CHOOSE_FOLDER",
}

interface StreamlitEvent {
  type: StreamlitEventType
  target: File | Folder | (File | Folder)[]
}

interface State {
  numClicks: number
  isFocused: boolean
}

interface IArgs {
  files: File[]
  path: string
  artifacts_download_site: string
  show_download_file: boolean
  show_delete_file: boolean
  show_choose_folder: boolean
  show_choose_file: boolean
  show_new_folder: boolean
  show_upload_file: boolean
  show_rename_folder: boolean
  show_rename_file: boolean
  ignore_file_select_event: boolean
  ignore_folder_select_event: boolean
  static_file_server_path: string
}

const noticeStreamlit = (event: StreamlitEvent | StreamlitEvent[]) =>
  Streamlit.setComponentValue(event)

class FileBrowserStaticServer extends StreamlitComponentBase<State> {
  private args: IArgs

  constructor(props: ComponentProps) {
    super(props)
    this.args = props.args
  }

  ajustHeight(revoke_step?: number) {
    Streamlit.setFrameHeight()
  }

  componentDidMount(): void {
    const root = this.args.path
    const args = this.args
    window.addEventListener("message", function (event) {
      // console.log('从 iframe 中传递过来的点击事件:', event.data);
      if (
        event.data?.event === "filebrowser_file_selected" ||
        event.data?.event === "filebrowser_dir_selected" ||
        event.data?.event === "filebrowser_file_double_selected" ||
        event.data?.event === "filebrowser_path_changed" ||
        event.data?.event === "filebrowser_file_choose"
      ) {
        const file: File = {
          path: get(event, "data.data.file.path", ""),
        }
        get(event, "data.data.file.name", "") &&
          (file.name = get(event, "data.data.file.name", ""))
        get(event, "data.data.file.size", 0) &&
          (file.size = get(event, "data.data.file.size", 0))
        get(event, "data.data.file.create_time", 0) &&
          (file.create_time = get(event, "data.data.file.create_time", 0))
        get(event, "data.data.file.update_time", 0) &&
          (file.update_time = get(event, "data.data.file.update_time", 0))
        get(event, "data.data.file.access_time", 0) &&
          (file.access_time = get(event, "data.data.file.access_time", 0))

        event.data?.event === "filebrowser_file_selected" &&
          noticeStreamlit({
            type: StreamlitEventType.SELECT_FILE,
            target: file,
          })
        event.data?.event === "filebrowser_dir_selected" &&
          noticeStreamlit({
            type: StreamlitEventType.SELECT_FOLDER,
            target: file,
          })
        const { show_choose_file, show_choose_folder } = args
        event.data?.event === "filebrowser_file_double_selected" &&
          show_choose_file &&
          noticeStreamlit({
            type: StreamlitEventType.CHOOSE_FILE,
            target: [file],
          })
        event.data?.event === "filebrowser_file_choose" &&
          show_choose_file &&
          noticeStreamlit({
            type: StreamlitEventType.CHOOSE_FILE,
            target: [file],
          })
        event.data?.event === "filebrowser_folder_choose" &&
          show_choose_folder &&
          noticeStreamlit({
            type: StreamlitEventType.CHOOSE_FOLDER,
            target: [file],
          })
        event.data?.event === "filebrowser_path_changed" &&
          noticeStreamlit({
            type: StreamlitEventType.SELECT_FOLDER,
            target: file,
          })
      }
    })
    this.ajustHeight()
  }

  componentDidUpdate() {
    this.ajustHeight()
  }

  onResized = (size: any) => {
    this.ajustHeight()
  }

  public render = () => {
    return (
      <IframeResizer
        {...this.args}
        checkOrigin={false}
        autoResize
        onResized={this.onResized}
        frameBorder={0}
        style={{ width: "100%" }}
        src={this.args.static_file_server_path}
      />
    )
  }
}

class FileBrowserNative extends StreamlitComponentBase<State> {
  private args: IArgs

  constructor(props: ComponentProps) {
    super(props)
    this.args = props.args
  }

  ajustHeight(revoke_step?: number) {
    const root = document.getElementById("root")
    if (root) {
      const height = Math.min(
        root.clientHeight,
        root.scrollHeight,
        root.offsetHeight
      )
      Streamlit.setFrameHeight(height - (revoke_step ? revoke_step : 0))
      setTimeout(Streamlit.setFrameHeight, 1)
    }
  }

  componentDidMount() {
    this.ajustHeight()
  }

  componentDidUpdate() {
    this.ajustHeight()
  }

  folderOpenHandler = (opts: FileBrowserFolder) => this.ajustHeight()
  folderCloseHandler = (opts: FileBrowserFolder) => this.ajustHeight()

  fileSelectedHandler = (opts: FileBrowserFile) => {
    if (!this.args.ignore_file_select_event) {
      const file = this.args.files.find((file) => file.path === opts.key)
      file &&
        noticeStreamlit({ type: StreamlitEventType.SELECT_FILE, target: file })
    }
  }

  folderSelectedHandler = (opts: FileBrowserFolder) => {
    if (!this.args.ignore_folder_select_event) {
      const files = this.args.files.filter(
        (file) => file.path !== opts.key && file.path.startsWith(opts.key)
      )
      files &&
        noticeStreamlit({
          type: StreamlitEventType.SELECT_FOLDER,
          target: { path: opts.key },
        })
    }
  }

  downlandHandler = (keys: string[]) => {
    const files = this.args.files.filter((file) => keys.includes(file.path))
    files.forEach((file) => {
      let url = new URL(file.path, this.args.artifacts_download_site).toString()
      let filename = url.substring(url.lastIndexOf("/") + 1)
      let a = document.createElement("a")
      a.target = "_blank"
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.parentNode?.removeChild(a)
    })
    files.length &&
      noticeStreamlit({ type: StreamlitEventType.DOWNLOAD, target: files })
  }

  deleteFileHandler = (fileKey: string | string[]) => {
    const files = this.args.files.filter((file) =>
      typeof fileKey === "string"
        ? fileKey === file.path
        : fileKey.includes(file.path)
    )
    console.log("deleteFileHandler", "key", fileKey, "files ", files)

    files.length &&
      noticeStreamlit({ type: StreamlitEventType.DELETE_FILE, target: files })

    const remainingFiles = this.args.files.filter((file) =>
      typeof fileKey === "string"
        ? fileKey !== file.path
        : !fileKey.includes(file.path)
    )
    this.args.files = remainingFiles
  }

  createFolderHandler = (folderKey: string) => {
    noticeStreamlit({
      type: StreamlitEventType.CREATE_FOLDER,
      target: { path: folderKey },
    })
  }

  chooseHandler = (keys: string[]) => {
    const folders = keys
      .filter((key) => key.endsWith("/"))
      .map((key) => ({ path: key }))

    const files = this.args.files.filter(
      (file) => keys.includes(file.path) && !file.path.endsWith("/")
    )

    if (folders.length && !files.length) {
      return noticeStreamlit({
        type: StreamlitEventType.CHOOSE_FOLDER,
        target: folders,
      })
    }

    if (files.length && !folders.length) {
      return noticeStreamlit({
        type: StreamlitEventType.CHOOSE_FILE,
        target: files,
      })
    }

    if (files.length && folders.length) {
      return noticeStreamlit([
        {
          type: StreamlitEventType.CHOOSE_FOLDER,
          target: folders,
        },
        {
          type: StreamlitEventType.CHOOSE_FILE,
          target: files,
        },
      ])
    }
  }

  renameFileHandler = (oldFileKey: string, newFileKey: string) => {
    const file = this.args.files.find((file) => file.path === oldFileKey)
    file &&
      noticeStreamlit({
        type: StreamlitEventType.RENAME_FILE,
        target: { path: newFileKey, name: file.name },
      })
  }

  renameFolderHandler = (oldFolderKey: string, newFolderKey: string) => {
    console.log("renameFolderHandler", oldFolderKey, newFolderKey)
    const file = this.args.files.find(
      (file) =>
        file.path.substring(0, file.path.lastIndexOf("/") + 1) === oldFolderKey
    )
    file &&
      noticeStreamlit({
        type: StreamlitEventType.RENAME_FOLDER,
        target: {
          path: newFolderKey,
          name: file.path.substring(0, file.path.lastIndexOf("/") + 1),
        },
      })
  }

  convertFiles = (files: File[]): FileBrowserFile[] =>
    files.map((file) => ({
      key: file.path,
      modified: file.update_time || 0,
      size: file.size || 0,
    }))

  noop = () => <></>
  public render = () => {
    return (
      <div>
        <FileBrowser
          {...this.args}
          showActionBar
          canFilter={true}
          detailRenderer={this.noop}
          icons={Icons.FontAwesome(4)}
          files={this.convertFiles(this.args.files)}
          onFolderOpen={this.folderOpenHandler}
          onFolderClose={this.folderCloseHandler}
          onSelect={this.fileSelectedHandler}
          onSelectFolder={this.folderSelectedHandler}
          onDownloadFile={this.downlandHandler}
          onDeleteFile={this.deleteFileHandler}
          onCreateFolder={this.createFolderHandler}
          onRenameFile={this.renameFileHandler}
          onRenameFolder={this.renameFolderHandler}
          actionRenderer={(...args: IActionsProps[]) => {
            return Actions({
              ...args[0],
              ...{
                canChooseFile: this.args.show_choose_file,
                canChooseFolder: this.args.show_choose_folder,
                canCreateFolder: this.args.show_new_folder,
                canRenameFile: this.args.show_rename_file,
                canRenameFolder: this.args.show_rename_folder,
                canDownloadFile:
                  this.args.show_download_file &&
                  !!this.args.artifacts_download_site,
                canDeleteFile: this.args.show_delete_file,
                onChooseFolder: () =>
                  this.chooseHandler(args[0].selectedItems.map((i) => i.key)),
                onChooseFile: () =>
                  this.chooseHandler(args[0].selectedItems.map((i) => i.key)),
                onDeleteFile: () =>
                  this.deleteFileHandler(
                    args[0].selectedItems.map((i) => i.key)
                  ),
              },
            }) as JSX.Element
          }}
        />
      </div>
    )
  }
}
const StreamlitFileBrowserNative = withStreamlitConnection(FileBrowserNative)
const StreamlitFileBrowserStaticServer = withStreamlitConnection(
  FileBrowserStaticServer
)

class FileBrowserWrapper extends StreamlitComponentBase<State> {
  private args: IArgs

  constructor(props: ComponentProps) {
    super(props)
    this.args = props.args
  }

  public render(): React.ReactNode {
    if (this.args.static_file_server_path) {
      return (
        <div>
          <StreamlitFileBrowserStaticServer {...this.props} />
        </div>
      )
    } else {
      return (
        <div>
          <StreamlitFileBrowserNative {...this.props} />
        </div>
      )
    }
  }
}

export default withStreamlitConnection(FileBrowserWrapper)
