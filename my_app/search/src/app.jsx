import React from 'react'
import { formShape } from 'rc-form'
import createForm from 'rc-form/lib/createDOMForm'
import { Segment, Grid, Form, Button } from 'semantic-ui-react'
import Search from './search.jsx'

import './style.css'

const datasheet = {}

class OriginApp extends React.Component {
  static propTypes = {
    form: formShape,
  };

  constructor (props) {
    super(props)
  }

  componentDidMount () {
    this.props.form.setFieldsValue(datasheet)
    const projectApi = 'http://182.61.145.178:3000/stage/api/projects/'
    fetch(projectApi)
      .then((response) => {
        if (response.status !== 200) {
          throw new Error('Fail to get response with status ' + response.status)
        }
        response.json()
          .then((responseJson) => {
            if (responseJson) {
              const source = responseJson.map((item, index, array) => {
                item.tabIndex = '0'
                return item
              })
              this.setState({ source })
            }
          })
          .catch((error) => {
            this.setState({ source: null })
            console.log(error)
          })
          .catch((error) => {
            this.setState({ source: null })
            console.log(error)
          })
      })
  }

  render () {
    const { getFieldDecorator, getFieldError } = this.props.form
    return (
      <form className='ui form'>
        <Form.Field>
          <Grid>
            <Grid.Column width={16}>
              {getFieldDecorator('selected', {
                initialValue: '',
                rules: [{
                  required: true,
                  message: '请输入搜索关键词'
                }]
              })(<Search
                   {...this.props}
                   {...this.state}
                   fluid
                   icon={<Button primary icon='search'></Button>}
              />)}
            </Grid.Column>
          </Grid>
        </Form.Field>
      </form>
    )
  }
}

const App = createForm({
  onFieldsChange (_, changedFields, allFields) {
    console.log('onFieldsChange: ', changedFields, allFields)
  },
  onValuesChange (_, changedValues, allValues) {
    console.log('onValuesChange: ', changedValues, allValues)
  }
})(OriginApp)

export default App
