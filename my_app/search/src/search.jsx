import React from 'react'
import { Search, Label } from 'semantic-ui-react'

import PropTypes from 'prop-types'
import _ from 'lodash'

const resultRenderer = ({ title }) => <Label content={title} />

resultRenderer.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string
}

const initialState = { isloading: false, results: [], value: '', open: false,
  segmentations: [] }

class MySearch extends React.Component {
  state = initialState

  handleResultSelect = (e, { result }) => {
    this.setState({ value: result.title, open: false, })
    this.setSelected(result.title)
  }

  handleSearchChange = (e, { value }) => {
    this.setState({ isLoading: true, value })
    setTimeout(() => this.handleSegment(this.state.value))

    setTimeout(() => {
      if (this.state.value.length < 1) return this.setState(
        initialState)

      const isMatch = result => this.state.segmentations.every((item,
        index, array) => {
        return new RegExp(item)
          .test(result.title)
      })

      this.setState({
        isLoading: false,
        results: _.filter(this.props.source, isMatch),
        open: Boolean(value.length)
      })

    }, 500)

    this.setSelected(value)
  }

  handleBlurSearch = (e) => {
    if (!e.relatedTarget) { var open = false } else if (e.relatedTarget && e
      .relatedTarget.classList) {
      open = _.includes(e.relatedTarget.classList, 'result');
    }
    this.setState({ open: open, focused: false, });
  }

  handleFocusSearch = (e) => {
    this.setState({ open: true, focused: true, });
  }

  handleSegment = (search) => {
    const segmentationApi =
      'http://182.61.145.178:3000/stage/api/segmentations/';
    fetch(segmentationApi, {
        method: 'POST',
        headers: {
          'Content-type': 'application/json'
        },
        body: JSON.stringify({ search })
      })
      .then((response) => (response.json())
        .then((responseJsonData) => {
          console.log(responseJsonData)
          this.setState({ segmentations: responseJsonData.filter((item,
              index, array) => (item.length > 1)) })
        })
        .catch((error) => {
          console.log(error);
        })
      )
  }

  setSelected = (value) => {
    this.props.form.setFieldsValue({
      selected: value,
    })
  }

  render() {
    const { placeholder, ...rest } = this.props;
    const { isLoading, results } = this.state;

    return (
      <Search
        loading={isLoading}
        onResultSelect={this.handleResultSelect}
        onSearchChange={_.debounce(this.handleSearchChange, 500, {
          leading: true
        })}
        results={results}
        resultRenderer={resultRenderer}
        placeholder={placeholder}
        open={this.state.open}
        onFocus={this.handleFocusSearch}
        onBlur={this.handleBlurSearch}
        showNoResults={false}
        {...rest}
      />
    )
  }
}

export default MySearch
