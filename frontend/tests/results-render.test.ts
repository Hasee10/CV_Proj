import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Routes, Route, Outlet } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { CapturedResults } from '../src/pages/CapturedResults';
import { Benchmark } from '../src/pages/Benchmark';
import { readFileSync } from 'node:fs';
import type { CaptureManifest } from '../src/api/results';

const asset=(path:string)=>new URL('../public'+path,import.meta.url);
const latest=JSON.parse(readFileSync(asset('/results/latest.json'),'utf8'));
const manifest=JSON.parse(readFileSync(asset(latest.manifest),'utf8')) as CaptureManifest;
const responses=Object.fromEntries(manifest.records.map(r=>[r.id,JSON.parse(readFileSync(asset(r.response),'utf8'))]));
function render(page:ReturnType<typeof createElement>,loading=false){
  function Layout(){return createElement(Outlet,{context:{readiness:'ready',capture:{loading,manifest:loading?null:manifest,responses:loading?{}:responses,error:null}}});}
  return renderToStaticMarkup(createElement(MemoryRouter,null,createElement(Routes,null,createElement(Route,{element:createElement(Layout)},createElement(Route,{path:'/',element:page})))));
}
describe('Results page loading and captured content',()=>{
  it('renders loading safely when both selection and fresh result are absent',()=>{
    expect(render(createElement(CapturedResults,{kind:'verification'}),true)).toContain('Loading captured backend results');
  });
  it('renders the actual verification decision and untouched notice',()=>{
    const html=render(createElement(CapturedResults,{kind:'verification'}));
    expect(html).toContain('Amounts agree');expect(html).toContain('Saved API capture');expect(html).toContain(responses.sheet_accept.request_id);
  });
  it('renders the actual numeric baseline text and decimal string',()=>{
    const html=render(createElement(CapturedResults,{kind:'recognition'}));
    expect(html).toContain(responses['numeric-baseline'].raw_text);expect(html).toContain(responses['numeric-baseline'].parsed_value);
  });
  it('separates genuine and synthetic benchmark groups',()=>{
    const html=render(createElement(Benchmark));expect(html).toContain('GENUINE HANDWRITING');expect(html).toContain('SYNTHETIC');expect(html).toContain('0.2521');
  });
});
