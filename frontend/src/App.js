import React, {Component} from 'react';
import {Row, Col} from 'react-bootstrap';
import {Table, Column, Cell} from 'fixed-data-table';
import 'fixed-data-table/dist/fixed-data-table.css';

import utils from './utils';
import './App.css';

const REST_PREFIX = '/rest/v1';

function ajax(url, successHandler) {
    url = REST_PREFIX + url;
    return (
        fetch(url)
        .then(response => {
            if (response.ok) {
                console.log('success');
                return response.json();
            } else {
                throw response.status;
            }
        })
        .then(successHandler)
        .catch(error => {
            console.log(error);
        }));
}

class App extends Component {
  render() {
    return (
        <Row>
            <Col xs={12} md={8}>
                <DataTable
                    dataUrl={'/activities/?client_web_key='
                                + new URLSearchParams(window.location.search)
                                                    .get('client_web_key')}
                    sortKey={['-started_at', 'task__short_desc', 'id']}
                    fields={[
                        {
                            key: 'started_at',
                            header: 'Date',
                            type: 'date',
                            width: 100,
                        },
                        {
                            key: 'task__short_desc',
                            header: 'Description',
                            type: 'text',
                            width: 500,
                        },
                        {
                            key: 'hours',
                            type: 'number',
                            decimals: 2,
                            width: 60,
                        },
                    ]}
                />
            </Col>
        </Row>
    );
  }
}

class DataTable extends Component {
    constructor() {
        super();
        this.state = {
            dataRows: [],
        };
    }

    getCell({fieldObj, rowIndex, width, height}) {
        if (!this.state.dataRows[rowIndex]) return '';

        let val = this.state.dataRows[rowIndex].get(fieldObj.key);

        if (fieldObj.type === 'number') {
            val = Number.parseFloat(val).toFixed(fieldObj.decimals);
        } else if (fieldObj.type === 'date') {
            val = val.slice(0, 10);
        }

        return <Cell>{val}</Cell>;
    }

    processDataRows(dataRows) {
        for (let rowObj of dataRows) {
            rowObj.get = utils.keyLookup.bind(rowObj);
        };
        dataRows = this.sortedDataRows(dataRows);
        return dataRows;
    }

    sortedDataRows(dataRows) {
        dataRows.sort((x,y) => {
            for (let key of this.props.sortKey) {
                let sign = 1;
                if (key[0] === '-') {
                    sign = -1;
                    key = key.slice(1);
                }

                if (x.get(key) < y.get(key)) return sign * (-1);
                if (x.get(key) > y.get(key)) return sign * (+1);
            }
            return 0;
        });
        return dataRows;
    }

    componentDidMount() {
        ajax(
            this.props.dataUrl,
            dataRows => this.setState({
                dataRows: this.processDataRows(dataRows)
            })
        );
    }

    render() {
        let columns = [];
        for (let fieldObj of this.props.fields) {
            let header = null;
            if (fieldObj.header) header = fieldObj.header;
            else header = utils.getHrFieldName(fieldObj.key);
            let width = fieldObj.width;

            let column = (
                <Column
                    key={fieldObj.key}
                    header={header}
                    cell={args => this.getCell({fieldObj, ...args})}
                    width={width}
                />
            );
            columns.push(column);
        }
        return (
            <Table
                rowHeight={30}
                rowsCount={this.state.dataRows.length}
                width={800}
                maxHeight={5500}
                headerHeight={50}
            >
                {columns}
            </Table>
        );
    }
}

export default App;
