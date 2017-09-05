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
                    dataUrl='/activities/'
                    fields={[
                        {   
                            key: 'id',
                            type: 'text',
                            width: 100,
                        },
                        {
                            key: 'task__short_desc',
                            type: 'text',
                            width: 350,
                        },
                        {
                            key: 'hours',
                            type: 'number',
                            decimals: 2,
                            width: 80,
                        },
                        {
                            key: 'started_at',
                            type: 'date',
                            width: 100,
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
        let keys = fieldObj.key.split(/__/);
        let type = fieldObj.type;

        if (!this.state.dataRows[rowIndex]) return '';

        let val = this.state.dataRows[rowIndex];
        for (let key of keys) {
            val = val[key];
        }

        if (type === 'text') {
            ;
        } else if (type === 'number') {
            val = Number.parseFloat(val).toFixed(fieldObj.decimals);
        } else if (type === 'date') {
            val = val.slice(0, 10);
        }

        return <Cell>{val}</Cell>;
    }

    componentDidMount() {
        ajax(
            this.props.dataUrl,
            dataRows => this.setState({dataRows})
        );
    }

    render() {
        let columns = [];
        for (let fieldObj of this.props.fields) {
            let header = utils.getHrFieldName(fieldObj.key);
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
                rowHeight={50}
                rowsCount={this.state.dataRows.length}
                width={800}
                height={500}
                headerHeight={50}
            >
                {columns}
            </Table>
        );
    }
}

export default App;
