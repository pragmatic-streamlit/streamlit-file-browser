import React from "react"
import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import FileBrowser, { Icons, FileBrowserFile, FileBrowserFolder } from 'react-keyed-file-browser';
import Actions from './actions';
import 'react-keyed-file-browser/dist/react-keyed-file-browser.css';
import 'font-awesome/css/font-awesome.min.css';

interface File {
  name: string;
  path: string;
  size: number;
  create_time: number;
  update_time: number;
  access_time: number;
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
}

interface StreamlitEvent {
  type: StreamlitEventType;
  target: File | File[];
}

interface State {
  numClicks: number
  isFocused: boolean
}

interface IArgs {
  files: File[]
  artifacts_site: string
  show_download_file: boolean
  show_choose_file: boolean
}

const noticeStreamlit = (event: StreamlitEvent) => Streamlit.setComponentValue(event)

const getTimeDiff = (time: number) => (+new Date() - time);

class FileBrowserWrapper extends StreamlitComponentBase<State> {
  private args: IArgs

  constructor(props: ComponentProps) {
    super(props)
    this.args = props.args
  }

  ajustHeight(revoke_step?: number) {
    const root = document.getElementById('root');
    if (root) {
      const height = Math.min(root.clientHeight, root.scrollHeight, root.offsetHeight);
      Streamlit.setFrameHeight(height - (revoke_step ? revoke_step : 0));
      setTimeout(Streamlit.setFrameHeight, 1);
    }
  }

  componentDidMount() {
    this.ajustHeight();
  }

  componentDidUpdate() {
    this.ajustHeight();
  }

  folderOpenHandler = (opts: FileBrowserFolder) => this.ajustHeight();
  folderCloseHandler = (opts: FileBrowserFolder) => this.ajustHeight();

  fileSelectedHandler = (opts: FileBrowserFile) => {
    const file = this.args.files.find(file => file.path === opts.key)
    file && noticeStreamlit({ type: StreamlitEventType.SELECT_FILE, target: file });
  }

  downlandHandler = (keys: string[]) => {
    const files = this.args.files.filter(file => keys.includes(file.path))
    files.forEach(file => {
      let url = new URL(file.path, `${this.args.artifacts_site}/download/artifacts/`).toString();
      let filename = url.substring(url.lastIndexOf('/')+1);
      let a = document.createElement('a');
      a.target = "_blank";
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.parentNode?.removeChild(a);
    });
    files.length && noticeStreamlit({ type: StreamlitEventType.DOWNLOAD, target: files });
  }

  chooseHandler = (keys: string[]) => {
    const files = this.args.files.filter(file => keys.includes(file.path))
    files.length && noticeStreamlit({ type: StreamlitEventType.CHOOSE_FILE, target: files });
  }

  convertFiles = (files: File[]): FileBrowserFile[] => (
    files.map(file => (
      {
        key: file.path,
        modified: getTimeDiff(file.update_time),
        size: file.size,
      }
    ))
  )

  noop = () => <></>
  public render = () => {
    let that = this;
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
          onDownloadFile={this.downlandHandler}
          actionRenderer={(...args: any) => {
            return Actions({
              ...args[0],
              ...{
              canChooseFile: that.args.show_choose_file,
              canDownloadFile: that.args.show_download_file && that.args.artifacts_site,
              onChooseFile: (keys: string[]) => that.chooseHandler(args[0].selectedItems.map((i: any) => i.key))
            }})
            }
          }
        />
      </div>
    )
  }
}

export default withStreamlitConnection(FileBrowserWrapper)
